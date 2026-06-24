from django.contrib import admin

from .models import SalesFile, UploadBatch


class SalesFileInline(admin.TabularInline):
    model = SalesFile
    extra = 0
    readonly_fields = ('original_name', 'status', 'row_count', 'uploaded_at', 'error_message')


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'row_count', 'uploaded_at')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('id', 'notes')
    readonly_fields = ('uploaded_at', 'error_message', 'row_count')
    inlines = (SalesFileInline,)


@admin.register(SalesFile)
class SalesFileAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'batch', 'status', 'row_count', 'uploaded_at')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('original_name', 'file', 'notes')
    readonly_fields = ('uploaded_at', 'error_message', 'row_count')
