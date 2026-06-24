from io import BytesIO

import pandas as pd

from dashboard.services.analytics import build_analytics_payload


def _safe_value(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def safe_export_dataframe(dataframe):
    exported = dataframe.copy()
    object_columns = exported.select_dtypes(include=['object']).columns
    for column in object_columns:
        exported[column] = exported[column].map(_safe_value)
    return exported


def dataframe_to_csv(dataframe):
    return safe_export_dataframe(dataframe).to_csv(index=False).encode('utf-8-sig')


def dataframe_to_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        safe_export_dataframe(dataframe).to_excel(writer, sheet_name='Merged Data', index=False)
    return output.getvalue()


def analytics_summary_csv(dataframe):
    payload = build_analytics_payload(dataframe)
    rows = [
        ('Total Revenue', payload['kpis']['revenue']),
        ('Total Profit', payload['kpis']['profit']),
        ('Total Orders', payload['kpis']['orders']),
        ('Total Customers', payload['kpis']['customers']),
        ('Average Transaction', payload['kpis']['average_transaction']),
        ('Merged Rows', payload['row_count']),
    ]
    rows.extend((f'Insight {index}', insight) for index, insight in enumerate(payload['insights'], start=1))
    return pd.DataFrame(rows, columns=['Metric', 'Value']).to_csv(index=False).encode('utf-8-sig')
