import csv
import os
import re
import json
import pandas as pd


from django.shortcuts import render, redirect

from .forms import UploadForm
from .models import SalesFile
from datetime import datetime
from collections import defaultdict
from dashboard.services.analytics import build_analytics_payload


def normalize_column(column_name):
    return re.sub(r'[^a-z0-9]', '', str(column_name or '').lower())


def find_column(columns, candidates):
    normalized_columns = {normalize_column(col): col for col in columns if col is not None}
    for candidate in candidates:
        candidate_key = normalize_column(candidate)
        for normalized, original in normalized_columns.items():
            if normalized == candidate_key or candidate_key in normalized or normalized in candidate_key:
                return original
    return None


def parse_numeric(value):
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if text == '':
        return 0.0

    text = text.replace('$', '').replace(',', '')
    if text.startswith('(') and text.endswith(')'):
        text = '-' + text[1:-1]

    try:
        return float(text)
    except ValueError:
        return 0.0


def read_csv_file(path):
    with open(path, newline='', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        columns = reader.fieldnames or []
    return rows, columns


def aggregate_by_label(rows, label_column, value_column, keywords):
    if not label_column or not value_column:
        return 0.0

    keywords = [normalize_column(keyword) for keyword in keywords]
    total = 0.0

    for row in rows:
        label = normalize_column(row.get(label_column, ''))
        if not label:
            continue
        if any(keyword in label for keyword in keywords):
            total += parse_numeric(row.get(value_column))

    return total


def compute_kpis(file_path):
    rows, columns = read_csv_file(file_path)

    if not rows:
        return {
            'revenue': 0,
            'profit': 0,
            'orders': 0,
            'customers': 0,
        }

    def detect_column(columns, keywords):
        best_match = None
        best_score = 0

        for col in columns:
            normalized = normalize_column(col)

            score = 0
            for keyword in keywords:
                keyword = normalize_column(keyword)

                if normalized == keyword:
                    score += 100
                elif keyword in normalized:
                    score += 50
                elif normalized in keyword:
                    score += 25

            if score > best_score:
                best_score = score
                best_match = col

        return best_match

    revenue_column = detect_column(columns, [
        'sales',
        'revenue',
        'sales amount',
        'sales value',
        'net sales',
        'gross sales',
        'total sales',
        'turnover',
        'amount',
        'income'
    ])

    profit_column = detect_column(columns, [
        'profit',
        'net profit',
        'gross profit',
        'earnings',
        'margin'
    ])

    order_column = detect_column(columns, [
        'order id',
        'order',
        'invoice',
        'invoice id',
        'transaction',
        'transaction id'
    ])

    customer_column = detect_column(columns, [
        'customer',
        'customer id',
        'client',
        'buyer',
        'consumer'
    ])

    revenue = 0
    profit = 0

    if revenue_column:
        revenue = sum(
            parse_numeric(row.get(revenue_column))
            for row in rows
        )

    if profit_column:
        profit = sum(
            parse_numeric(row.get(profit_column))
            for row in rows
        )

    if order_column:
        orders = len({
            row.get(order_column)
            for row in rows
            if row.get(order_column)
        })
    else:
        orders = len(rows)

    if customer_column:
        customers = len({
            row.get(customer_column)
            for row in rows
            if row.get(customer_column)
        })
    else:
        customers = 0

    print("Detected Revenue Column:", revenue_column)
    print("Detected Profit Column:", profit_column)
    print("Detected Order Column:", order_column)
    print("Detected Customer Column:", customer_column)

    return {
        'revenue': round(revenue, 2),
        'profit': round(profit, 2),
        'orders': orders,
        'customers': customers,
    }


def home(request):
    revenue = 0
    profit = 0
    orders = 0
    customers = 0

    latest_file = SalesFile.objects.last()

    if latest_file:
        try:
            kpis = compute_kpis(latest_file.file.path)
            revenue = kpis['revenue']
            profit = kpis['profit']
            orders = kpis['orders']
            customers = kpis['customers']
        except Exception as e:
            print(f'KPI parse error: {e}')

    context = {
        'revenue': revenue,
        'profit': profit,
        'orders': orders,
        'customers': customers,
    }

    return render(request, 'dashboard/home.html', context)


def upload_data(request):
    form = UploadForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        uploaded_files = form.cleaned_data['files']
        override_existing = form.cleaned_data.get('override_existing', False)

        for uploaded_file in uploaded_files:
            filename = os.path.basename(uploaded_file.name)

            if override_existing:
                existing_files = SalesFile.objects.filter(file__iendswith=filename)
                for existing in existing_files:
                    existing.file.delete(save=False)
                existing_files.delete()

            SalesFile.objects.create(
                file=uploaded_file,
                original_name=uploaded_file.name,
                status=SalesFile.Status.COMPLETED
            )

        return redirect('home')

    return render(request, 'dashboard/upload.html', {'form': form})

def calculate_growth_rate(file_path):
    rows, columns = read_csv_file(file_path)

    date_column = find_column(
        columns,
        ['date', 'orderdate', 'order date', 'transaction date']
    )

    revenue_column = find_column(
        columns,
        ['sales', 'revenue', 'amount', 'turnover']
    )

    print("Date Column:", date_column)
    print("Revenue Column:", revenue_column)

    if not date_column or not revenue_column:
        return 0

    monthly_sales = defaultdict(float)

    for row in rows:
        try:
            date_value = str(row.get(date_column)).strip()
            sale_value = parse_numeric(row.get(revenue_column))

            dt = datetime.fromisoformat(date_value)

            month_key = f"{dt.year}-{dt.month:02d}"

            monthly_sales[month_key] += sale_value

        except Exception as e:
            print("Date Parse Error:", e)
            continue

    print("Monthly Sales:", dict(monthly_sales))

    months = sorted(monthly_sales.keys())
    print("Months:", months)

    if len(months) < 2:
        return 0

    current_month = monthly_sales[months[-1]]
    previous_month = monthly_sales[months[-2]]

    print("Current:", current_month)
    print("Previous:", previous_month)

    if previous_month == 0:
        return 0

    growth = ((current_month - previous_month) / previous_month) * 100

    return round(growth, 2)


def analytics(request):
    import pandas as pd

    context = {
        'total_transactions': 0,
        'avg_transaction': 0,
        'growth_rate': 0,
        'revenue': 0,
        'profit': 0,
        'source_file': None,
        'analytics': None,
    }

    latest_file = SalesFile.objects.last()

    if latest_file:
        try:
            # Load CSV into DataFrame
            df = pd.read_csv(latest_file.file.path)

            # Generate analytics payload
            analytics_payload = build_analytics_payload(df)

            # Existing KPI calculations
            kpis = compute_kpis(latest_file.file.path)

            total_transactions = kpis['orders']

            context.update({
                'source_file': latest_file,
                'analytics': analytics_payload,
                'total_transactions': total_transactions,
                'avg_transaction': round(
                    kpis['revenue'] / total_transactions, 2
                ) if total_transactions else 0,
                'growth_rate': calculate_growth_rate(
                    latest_file.file.path
                ),
                'revenue': kpis['revenue'],
                'profit': kpis['profit'],
            })

        except Exception as e:
            print("Analytics Error:", e)

    return render(request, 'dashboard/analytics.html', context)


def reports(request):
    reports_list = SalesFile.objects.all().order_by('-id')

    total_reports = reports_list.count()

    context = {
        'total_reports': total_reports,
        'pending_reports': 0,
        'completed_reports': total_reports,
        'failed_reports': 0,
        'reports': reports_list,
    }

    return render(request, 'dashboard/reports.html', context)



