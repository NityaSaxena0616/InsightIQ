import uuid

from django.db import models


class UploadBatch(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        PARTIAL = 'partial', 'Partially completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    row_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Upload {self.uploaded_at:%Y-%m-%d %H:%M}' if self.uploaded_at else str(self.id)


class SalesFile(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    batch = models.ForeignKey(
        UploadBatch,
        related_name='files',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    row_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.original_name or self.file.name
