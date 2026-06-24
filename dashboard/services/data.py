from pathlib import Path

import pandas as pd

from dashboard.models import SalesFile, UploadBatch


class NoDataError(ValueError):
    pass


def _unique_columns(columns):
    counts = {}
    unique = []
    for index, column in enumerate(columns, start=1):
        name = str(column).strip() if str(column).strip() else f'Column {index}'
        counts[name] = counts.get(name, 0) + 1
        unique.append(name if counts[name] == 1 else f'{name} {counts[name]}')
    return unique


def read_dataframe(path, source_name=None):
    extension = Path(path).suffix.lower()
    if extension == '.csv':
        try:
            dataframe = pd.read_csv(path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            dataframe = pd.read_csv(path, encoding='cp1252')
    elif extension in {'.xls', '.xlsx'}:
        dataframe = pd.read_excel(path)
    else:
        raise ValueError('Unsupported file type. Upload a CSV, XLS, or XLSX file.')

    if dataframe.columns.empty:
        raise ValueError('The spreadsheet must have a header row.')
    dataframe.columns = _unique_columns(dataframe.columns)
    dataframe = dataframe.dropna(how='all').reset_index(drop=True)
    if source_name:
        dataframe['Source File'] = source_name
    return dataframe


def concatenate_dataframes(dataframes):
    if not dataframes:
        raise NoDataError('No successfully processed data files are available.')
    return pd.concat(dataframes, ignore_index=True, sort=False)


def load_sales_files(sales_files):
    dataframes = [
        read_dataframe(item.file.path, item.original_name or Path(item.file.name).name)
        for item in sales_files
    ]
    return concatenate_dataframes(dataframes)


def get_latest_active_batch():
    return (
        UploadBatch.objects.filter(status__in=[UploadBatch.Status.COMPLETED, UploadBatch.Status.PARTIAL])
        .order_by('-uploaded_at')
        .first()
    )


def load_active_dataframe():
    batch = get_latest_active_batch()
    if batch:
        files = batch.files.filter(status=SalesFile.Status.COMPLETED).order_by('uploaded_at')
        return load_sales_files(files), batch

    legacy_file = SalesFile.objects.filter(
        status=SalesFile.Status.COMPLETED,
        batch__isnull=True,
    ).order_by('-uploaded_at').first()
    if legacy_file:
        return load_sales_files([legacy_file]), legacy_file
    raise NoDataError('Upload at least one valid CSV or Excel file to begin.')
