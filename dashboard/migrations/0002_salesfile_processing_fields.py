from django.db import migrations, models


def mark_existing_files_completed(apps, schema_editor):
    sales_file = apps.get_model('dashboard', 'SalesFile')
    sales_file.objects.update(status='completed')


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesfile',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='salesfile',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                ],
                default='pending',
                max_length=10,
            ),
        ),
        migrations.RunPython(mark_existing_files_completed, migrations.RunPython.noop),
        migrations.AddField(
            model_name='salesfile',
            name='error_message',
            field=models.TextField(blank=True),
        ),
    ]
