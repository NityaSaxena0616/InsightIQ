import re

import pandas as pd


COLUMN_ALIASES = {
    'revenue': ['sales', 'revenue', 'turnover', 'total income', 'gross revenue', 'gross sales'],
    'generic_value': ['amount', 'value', 'total amount'],
    'profit': ['profit', 'net profit', 'gross profit', 'operating profit', 'earnings'],
    'expense': ['expense', 'expenses', 'expenditure', 'total expenditure', 'cost'],
    'quantity': ['quantity', 'qty', 'units sold', 'units'],
    'unit_price': ['unit price', 'price', 'selling price', 'rate', 'cost per unit'],
    'order': ['order id', 'orderid', 'transaction id', 'transactionid', 'invoice id'],
    'customer': ['customer', 'customer name', 'customer id', 'customerid', 'client', 'client name', 'client id', 'clientid', 'buyer', 'email'],
    'date': ['order date', 'transaction date', 'invoice date', 'sale date', 'date', 'month', 'period'],
    'product': ['product', 'product name', 'item', 'item name', 'sku'],
    'region': ['region', 'sales region', 'territory', 'market', 'state', 'country'],
    'category': ['category', 'product category', 'segment', 'department'],
    'metric_label': ['variable name', 'variablename', 'variable code', 'variablecode', 'metric', 'description'],
    'metric_value': ['value', 'amount', 'total amount'],
}


def normalize_column(value):
    return re.sub(r'[^a-z0-9]', '', str(value or '').lower())


def matching_columns(dataframe, aliases):
    alias_values = COLUMN_ALIASES.get(aliases, aliases)
    normalized_aliases = [normalize_column(alias) for alias in alias_values]
    normalized_columns = {column: normalize_column(column) for column in dataframe.columns}

    exact = [
        column
        for alias in normalized_aliases
        for column, normalized in normalized_columns.items()
        if normalized == alias
    ]
    fuzzy = [
        column
        for alias in normalized_aliases
        for column, normalized in normalized_columns.items()
        if column not in exact and len(alias) >= 4 and (normalized.startswith(alias) or normalized.endswith(alias))
    ]
    return list(dict.fromkeys(exact + fuzzy))


def has_column(dataframe, aliases):
    return bool(matching_columns(dataframe, aliases))


def coalesce_series(dataframe, aliases, default=None):
    columns = matching_columns(dataframe, aliases)
    if not columns:
        return pd.Series(default, index=dataframe.index, dtype='object')

    result = dataframe[columns[0]].copy()
    for column in columns[1:]:
        result = result.combine_first(dataframe[column])
    return result


def numeric_series(dataframe, aliases):
    values = coalesce_series(dataframe, aliases, default=0)
    text = values.astype(str).str.strip()
    text = text.str.replace(r'^\((.*)\)$', r'-\1', regex=True)
    text = text.str.replace(r'[$,£€₹%]', '', regex=True)
    return pd.to_numeric(text, errors='coerce').fillna(0.0)


def date_series(dataframe):
    values = coalesce_series(dataframe, 'date')
    try:
        return pd.to_datetime(values, errors='coerce', format='mixed')
    except TypeError:
        return pd.to_datetime(values, errors='coerce')


def dimension_series(dataframe, aliases):
    values = coalesce_series(dataframe, aliases)
    return values.where(values.notna(), '').astype(str).str.strip()
