import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook

from .forms import UploadForm
from .models import SalesFile
from .views import compute_kpis_from_rows, read_tabular_file


class DashboardTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_all_pages_load(self):
        for url_name in ('home', 'upload', 'analytics', 'reports'):
            with self.subTest(url_name=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

    def test_sales_column_is_summed_as_revenue(self):
        rows = [{'Sales': '100'}, {'Sales': '150'}]
        self.assertEqual(compute_kpis_from_rows(rows, ['Sales'])['revenue'], 250)

    def test_form_rejects_unknown_extension(self):
        uploaded = SimpleUploadedFile('sales.txt', b'Sales\n100', content_type='text/plain')
        form = UploadForm(files={'file': uploaded})
        self.assertFalse(form.is_valid())
        self.assertIn('Unsupported file type', form.errors['file'][0])

    def test_csv_upload_is_processed_and_drives_analytics(self):
        content = (
            b'Order Date,Order ID,Customer,Sales,Profit\n'
            b'2026-01-10,1,Ada,100,20\n'
            b'2026-02-10,2,Grace,150,30\n'
        )
        uploaded = SimpleUploadedFile('sales.csv', content, content_type='text/csv')

        response = self.client.post(reverse('upload'), {'file': uploaded, 'notes': 'Monthly sales'})

        self.assertRedirects(response, reverse('home'))
        sales_file = SalesFile.objects.get()
        self.assertEqual(sales_file.status, SalesFile.Status.COMPLETED)
        self.assertEqual(sales_file.notes, 'Monthly sales')

        analytics = self.client.get(reverse('analytics'))
        self.assertEqual(analytics.context['total_transactions'], 2)
        self.assertEqual(analytics.context['avg_transaction'], 125)
        self.assertEqual(analytics.context['growth_rate'], '+50.0%')

    def test_xlsx_reader(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Order ID', 'Sales'])
        sheet.append([1, 75])
        data = BytesIO()
        workbook.save(data)
        uploaded = SimpleUploadedFile(
            'sales.xlsx',
            data.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        sales_file = SalesFile.objects.create(file=uploaded)

        rows, columns = read_tabular_file(sales_file.file.path)

        self.assertEqual(columns, ['Order ID', 'Sales'])
        self.assertEqual(rows[0]['Sales'], 75)

    def test_invalid_workbook_is_recorded_as_failed(self):
        uploaded = SimpleUploadedFile(
            'broken.xlsx',
            b'not a workbook',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(reverse('upload'), {'file': uploaded})

        self.assertRedirects(response, reverse('home'))
        sales_file = SalesFile.objects.get()
        self.assertEqual(sales_file.status, SalesFile.Status.FAILED)
        self.assertTrue(sales_file.error_message)

    def test_reports_show_real_processing_counts(self):
        SalesFile.objects.create(file='uploads/complete.csv', status=SalesFile.Status.COMPLETED)
        SalesFile.objects.create(file='uploads/failed.csv', status=SalesFile.Status.FAILED)

        response = self.client.get(reverse('reports'))

        self.assertEqual(response.context['total_reports'], 2)
        self.assertEqual(response.context['completed_reports'], 1)
        self.assertEqual(response.context['failed_reports'], 1)
