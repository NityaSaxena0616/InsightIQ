from django.db import migrations, models
import django.db.models.deletion
import uuid


def populate_original_names(apps, schema_editor):
    sales_file = apps.get_model('dashboard', 'SalesFile')
    for item in sales_file.objects.filter(original_name=''):
        item.original_name = item.file.name.rsplit('/', 1)[-1]
        item.save(update_fields=['original_name'])


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0002_salesfile_processing_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadBatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('partial', 'Partially completed'), ('failed', 'Failed')], default='pending', max_length=10)),
                ('error_message', models.TextField(blank=True)),
                ('row_count', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='salesfile',
            name='batch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='files', to='dashboard.uploadbatch'),
        ),
        migrations.AddField(
            model_name='salesfile',
            name='original_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='salesfile',
            name='row_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(populate_original_names, migrations.RunPython.noop),
    ]
