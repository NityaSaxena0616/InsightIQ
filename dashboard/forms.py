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
        widget=MultipleFileInput(
            attrs={'accept': '.csv,.xls,.xlsx'}
        ),
    )

    business_context = forms.FileField(
        required=False,
        label='Business Events & Market Context',
        widget=forms.ClearableFileInput(
            attrs={
                'accept': '.pdf,.doc,.docx,.txt'
            }
        ),
        help_text='Upload a document describing market conditions, company actions, campaigns, competitors, festivals, or other business events.'
    )

    business_notes = forms.CharField(
        required=False,
        label='Manual Business Notes',
        widget=forms.Textarea(
            attrs={
                'rows': 6,
                'placeholder':
                    'Example:\n\n'
                    '- Jan 15: Increased product prices by 8%\n'
                    '- Mar 10: New competitor entered the market\n'
                    '- Aug 5: Diwali marketing campaign launched\n'
                    '- Sep 2: Supply chain disruption'
            }
        )
    )

    override_existing = forms.BooleanField(
        required=False,
        label='Replace earlier files with the same names after successful processing',
    )

    def clean_files(self):
        files = self.cleaned_data['files']

        allowed_extensions = {'.csv', '.xls', '.xlsx'}
        max_file_size = 10 * 1024 * 1024      # 10 MB
        max_total_size = 50 * 1024 * 1024     # 50 MB

        total_size = 0

        for uploaded_file in files:
            extension = Path(uploaded_file.name).suffix.lower()

            if extension not in allowed_extensions:
                raise forms.ValidationError(
                    f'{uploaded_file.name}: unsupported file type. Use CSV, XLS, or XLSX.'
                )

            if uploaded_file.size > max_file_size:
                raise forms.ValidationError(
                    f'{uploaded_file.name}: each file must be smaller than 10 MB.'
                )

            total_size += uploaded_file.size

        if total_size > max_total_size:
            raise forms.ValidationError(
                'The combined upload must be smaller than 50 MB.'
            )

        return files