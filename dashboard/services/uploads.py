from pathlib import Path

from dashboard.models import SalesFile, UploadBatch
from dashboard.services.analytics import calculate_kpis
from dashboard.services.data import concatenate_dataframes, read_dataframe


def process_upload_batch(uploaded_files, notes='', override_existing=False):
    batch = UploadBatch.objects.create(notes=notes, status=UploadBatch.Status.PENDING)
    dataframes = []
    successful_files = []
    errors = []

    for uploaded_file in uploaded_files:
        original_name = Path(uploaded_file.name).name
        sales_file = SalesFile.objects.create(
            batch=batch,
            file=uploaded_file,
            original_name=original_name,
            notes=notes,
            status=SalesFile.Status.PENDING,
        )
        try:
            dataframe = read_dataframe(sales_file.file.path, original_name)
        except Exception as exc:
            sales_file.status = SalesFile.Status.FAILED
            sales_file.error_message = str(exc)[:500]
            sales_file.save(update_fields=['status', 'error_message'])
            errors.append(f'{original_name}: {exc}')
            continue

        sales_file.status = SalesFile.Status.COMPLETED
        sales_file.row_count = len(dataframe)
        sales_file.error_message = ''
        sales_file.save(update_fields=['status', 'row_count', 'error_message'])
        successful_files.append(sales_file)
        dataframes.append(dataframe)

    if dataframes:
        merged = concatenate_dataframes(dataframes)
        calculate_kpis(merged)
        batch.row_count = len(merged)
        batch.status = UploadBatch.Status.PARTIAL if errors else UploadBatch.Status.COMPLETED
        if override_existing:
            names = [item.original_name for item in successful_files]
            replaced = SalesFile.objects.filter(original_name__in=names).exclude(batch=batch)
            for existing in replaced:
                existing.file.delete(save=False)
                existing.delete()
    else:
        merged = None
        batch.status = UploadBatch.Status.FAILED

    batch.error_message = '\n'.join(errors)[:2000]
    batch.save(update_fields=['status', 'row_count', 'error_message'])
    return batch, merged
