import pandas as pd

from dashboard.utils.columns import (
    coalesce_series,
    date_series,
    dimension_series,
    has_column,
    numeric_series,
)


def _round(value):
    return round(float(value), 2)


def _metric_table(dataframe):
    return has_column(dataframe, 'metric_label') and has_column(dataframe, 'metric_value')


def _metric_mask(dataframe, keywords):
    labels = dimension_series(dataframe, 'metric_label').str.lower()
    pattern = '|'.join(keywords)
    return labels.str.contains(pattern, regex=True, na=False)


def revenue_series(dataframe):
    if has_column(dataframe, 'revenue'):
        return numeric_series(dataframe, 'revenue')
    if has_column(dataframe, 'quantity') and has_column(dataframe, 'unit_price'):
        return numeric_series(dataframe, 'quantity') * numeric_series(dataframe, 'unit_price')
    if _metric_table(dataframe):
        values = numeric_series(dataframe, 'metric_value')
        return values.where(_metric_mask(dataframe, ['income', 'revenue', 'sales', 'turnover']), 0.0)
    return numeric_series(dataframe, 'generic_value')


def profit_series(dataframe):
    if has_column(dataframe, 'profit'):
        return numeric_series(dataframe, 'profit')
    if _metric_table(dataframe):
        values = numeric_series(dataframe, 'metric_value')
        direct_profit = values.where(_metric_mask(dataframe, ['profit', 'earnings']), 0.0)
        if direct_profit.sum() != 0:
            return direct_profit
    if has_column(dataframe, 'expense'):
        return revenue_series(dataframe) - numeric_series(dataframe, 'expense')
    return pd.Series(0.0, index=dataframe.index)


def calculate_kpis(dataframe):
    revenue = revenue_series(dataframe)
    profit = profit_series(dataframe)
    metric_table = _metric_table(dataframe)

    if has_column(dataframe, 'order'):
        orders = dimension_series(dataframe, 'order').replace('', pd.NA).nunique()
    else:
        orders = 0 if metric_table else len(dataframe)

    customers = (
        dimension_series(dataframe, 'customer').replace('', pd.NA).nunique()
        if has_column(dataframe, 'customer')
        else 0
    )
    return {
        'revenue': _round(revenue.sum()),
        'profit': _round(profit.sum()),
        'orders': int(orders),
        'customers': int(customers),
    }


def _group_values(dataframe, dimension, values, limit=12):
    if not has_column(dataframe, dimension):
        return {'labels': [], 'values': []}
    labels = dimension_series(dataframe, dimension).replace('', 'Unknown')
    grouped = values.groupby(labels).sum().sort_values(ascending=False).head(limit)
    return {'labels': grouped.index.tolist(), 'values': [_round(value) for value in grouped.tolist()]}


def get_monthly_revenue(dataframe):
    dates = date_series(dataframe)
    valid = dates.notna()
    if not valid.any():
        return {'labels': [], 'values': []}
    monthly = revenue_series(dataframe)[valid].groupby(dates[valid].dt.to_period('M')).sum().sort_index()
    return {
        'labels': [period.strftime('%b %Y') for period in monthly.index],
        'values': [_round(value) for value in monthly.tolist()],
    }


def get_product_distribution(dataframe):
    return _group_values(dataframe, 'product', revenue_series(dataframe), limit=10)


def get_region_sales(dataframe):
    return _group_values(dataframe, 'region', revenue_series(dataframe), limit=12)


def get_product_region_sales(dataframe):
    if not has_column(dataframe, 'product') or not has_column(dataframe, 'region'):
        return {'labels': [], 'datasets': []}
    working = pd.DataFrame({
        'product': dimension_series(dataframe, 'product').replace('', 'Unknown'),
        'region': dimension_series(dataframe, 'region').replace('', 'Unknown'),
        'revenue': revenue_series(dataframe),
    })
    top_products = working.groupby('product')['revenue'].sum().nlargest(8).index
    top_regions = working.groupby('region')['revenue'].sum().nlargest(6).index
    pivot = working[
        working['product'].isin(top_products) & working['region'].isin(top_regions)
    ].pivot_table(index='product', columns='region', values='revenue', aggfunc='sum', fill_value=0)
    pivot = pivot.reindex(index=top_products, columns=top_regions, fill_value=0)
    return {
        'labels': pivot.index.tolist(),
        'datasets': [
            {'label': str(region), 'data': [_round(value) for value in pivot[region].tolist()]}
            for region in pivot.columns
        ],
    }


def get_category_profit(dataframe):
    return _group_values(dataframe, 'category', profit_series(dataframe), limit=12)


def get_top_customers(dataframe):
    return _group_values(dataframe, 'customer', revenue_series(dataframe), limit=10)


def get_monthly_orders(dataframe):
    dates = date_series(dataframe)
    valid = dates.notna()
    if not valid.any():
        return {'labels': [], 'values': []}
    periods = dates[valid].dt.to_period('M')
    if has_column(dataframe, 'order'):
        orders = dimension_series(dataframe, 'order')[valid]
        grouped = orders.groupby(periods).nunique().sort_index()
    else:
        grouped = periods.groupby(periods).size().sort_index()
    return {
        'labels': [period.strftime('%b %Y') for period in grouped.index],
        'values': [int(value) for value in grouped.tolist()],
    }


def get_ai_insights(dataframe):
    insights = []
    region = get_region_sales(dataframe)
    product = get_product_distribution(dataframe)
    category = get_category_profit(dataframe)
    customer = get_top_customers(dataframe)
    monthly = get_monthly_revenue(dataframe)

    if region['labels']:
        insights.append(f"{region['labels'][0]} is the top revenue region at ${region['values'][0]:,.2f}.")
    if product['labels']:
        insights.append(f"{product['labels'][0]} is the best-selling product at ${product['values'][0]:,.2f}.")
    if category['labels']:
        insights.append(f"{category['labels'][0]} is the highest-profit category at ${category['values'][0]:,.2f}.")
    if customer['labels']:
        insights.append(f"{customer['labels'][0]} is the most valuable customer at ${customer['values'][0]:,.2f}.")
    if len(monthly['values']) >= 2 and monthly['values'][-2] != 0:
        growth = ((monthly['values'][-1] - monthly['values'][-2]) / abs(monthly['values'][-2])) * 100
        direction = 'grew' if growth >= 0 else 'declined'
        insights.append(f'Revenue {direction} {abs(growth):.1f}% in the latest month.')
    if not insights:
        insights.append('Add date, product, region, category, and customer columns for richer insights.')
    return insights


def apply_filters(dataframe, filters):
    filtered = dataframe.copy()
    dates = date_series(filtered)
    if filters.get('date_from'):
        start = pd.to_datetime(filters['date_from'], errors='coerce')
        if pd.notna(start):
            filtered = filtered[dates >= start]
            dates = dates.loc[filtered.index]
    if filters.get('date_to'):
        end = pd.to_datetime(filters['date_to'], errors='coerce')
        if pd.notna(end):
            filtered = filtered[dates <= end]

    for key in ('region', 'product', 'category'):
        selected = filters.get(key)
        if selected and has_column(filtered, key):
            values = dimension_series(filtered, key)
            filtered = filtered[values.str.casefold() == selected.casefold()]
    return filtered


def get_filter_options(dataframe):
    options = {}
    for key in ('region', 'product', 'category'):
        values = dimension_series(dataframe, key) if has_column(dataframe, key) else pd.Series(dtype='object')
        options[key] = sorted(value for value in values.dropna().unique().tolist() if value)
    dates = date_series(dataframe).dropna()
    options['date_min'] = dates.min().date().isoformat() if not dates.empty else ''
    options['date_max'] = dates.max().date().isoformat() if not dates.empty else ''
    return options


def build_analytics_payload(dataframe):
    kpis = calculate_kpis(dataframe)
    kpis['average_transaction'] = _round(kpis['revenue'] / kpis['orders']) if kpis['orders'] else 0
    return {
        'kpis': kpis,
        'charts': {
            'monthly_revenue': get_monthly_revenue(dataframe),
            'product_distribution': get_product_distribution(dataframe),
            'region_sales': get_region_sales(dataframe),
            'product_region_sales': get_product_region_sales(dataframe),
            'category_profit': get_category_profit(dataframe),
            'top_customers': get_top_customers(dataframe),
            'monthly_orders': get_monthly_orders(dataframe),
        },
        'insights': get_ai_insights(dataframe),
        'row_count': int(len(dataframe)),
    }
