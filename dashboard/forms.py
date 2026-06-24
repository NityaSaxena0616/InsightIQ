from pathlib import Path

from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super().clean(item, initial) for item in files if item]


class UploadForm(forms.Form):
    files = MultipleFileField(
        label='Sales Data Files',
        help_text='Select one or more CSV, XLS, or XLSX files (maximum 10 MB each).',
        widget=MultipleFileInput(attrs={'accept': '.csv,.xls,.xlsx'}),
    )
    notes = forms.CharField(
        label='Additional Notes',
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'placeholder': 'Optional notes about this upload batch.',
            }
        ),
    )
    override_existing = forms.BooleanField(
        required=False,
        label='Replace earlier files with the same names after successful processing',
    )

    def clean_files(self):
        files = self.cleaned_data['files']
        allowed_extensions = {'.csv', '.xls', '.xlsx'}
        max_file_size = 10 * 1024 * 1024
        max_total_size = 50 * 1024 * 1024

        for uploaded_file in files:
            extension = Path(uploaded_file.name).suffix.lower()
            if extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'{uploaded_file.name}: unsupported file type. Use CSV, XLS, or XLSX.'
                )
            if uploaded_file.size > max_file_size:
                raise forms.ValidationError(f'{uploaded_file.name}: each file must be smaller than 10 MB.')

        if sum(uploaded_file.size for uploaded_file in files) > max_total_size:
            raise forms.ValidationError('The combined upload must be smaller than 50 MB.')
        return files
