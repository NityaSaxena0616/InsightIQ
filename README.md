# InsightIQ

InsightIQ is a Django business-intelligence dashboard that accepts CSV, XLS, and XLSX sales data. It calculates revenue, profit, transaction, customer, average-order, and month-over-month growth metrics and maintains a processing history for uploaded reports.

## Local setup (Windows PowerShell)

```powershell
py -3.14 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and upload a spreadsheet whose first row contains column names. Recognized names include `Sales`, `Revenue`, `Profit`, `Order ID`, `Customer`, and `Order Date`. Month-over-month growth requires a date column and at least two calendar months.

## Tests

```powershell
python manage.py test
python manage.py check
```

## Production configuration

Set the variables shown in `.env.example` in the hosting environment. InsightIQ enables HTTPS redirect, secure cookies, and HSTS whenever `INSIGHTIQ_DEBUG=false`. Static files should be collected and served by the host or reverse proxy:

```powershell
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py check --deploy
```

Do not use the development secret or Django development server in production.
