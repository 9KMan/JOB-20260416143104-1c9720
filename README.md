# ERP System

A comprehensive Flask-based Enterprise Resource Planning (ERP) system covering Procurement, Goods Receiving, Production, Packaging, Sales, Financial, and Reporting modules.

## Features

- **Procurement Module**: Purchase orders, supplier management, RFQs
- **Goods Receiving**: GRN management, inspection workflow, warehouse receipts
- **Production Module**: Work orders, BOM, production scheduling
- **Packaging Module**: Packaging orders, label generation
- **Sales Module**: Customer orders, quotations, invoicing
- **Financial Module**: Chart of accounts, journal entries, ledger, trial balance, P&L, balance sheet
- **Reporting Module**: Dashboard with KPIs, inventory reports, financial reports

## Tech Stack

- **Backend**: Flask 3.0, Flask-SQLAlchemy, Flask-Migrate, Flask-RESTful
- **Database**: PostgreSQL
- **Authentication**: Flask-Login, Flask-WTF
- **Container**: Docker, docker-compose

## Quick Start

### Using Docker

```bash
docker-compose up --build
```

The application will be available at http://localhost:5000

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://erp_user:erp_password@localhost:5432/erp_db
export SECRET_KEY=your-secret-key

# Initialize database
flask db init
flask db migrate
flask db upgrade

# Run the application
python run.py
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/me` - Current user info

### Procurement
- `GET /procurement/suppliers` - List suppliers
- `POST /procurement/suppliers` - Create supplier
- `GET /procurement/purchase-orders` - List purchase orders
- `POST /procurement/purchase-orders` - Create purchase order

### Goods Receiving
- `GET /goods-receiving/goods-receipts` - List goods receipts
- `POST /goods-receiving/goods-receipts` - Create goods receipt
- `GET /goods-receiving/warehouses` - List warehouses

### Production
- `GET /production/work-orders` - List work orders
- `POST /production/work-orders` - Create work order
- `POST /production/work-orders/<id>/start` - Start work order
- `POST /production/work-orders/<id>/complete` - Complete work order

### Packaging
- `GET /packaging/packaging-orders` - List packaging orders
- `POST /packaging/packaging-orders` - Create packaging order

### Sales
- `GET /sales/customers` - List customers
- `POST /sales/customers` - Create customer
- `GET /sales/sales-orders` - List sales orders
- `POST /sales/sales-orders` - Create sales order
- `GET /sales/invoices` - List invoices

### Financial
- `GET /financial/accounts` - List accounts
- `POST /financial/accounts` - Create account
- `GET /financial/journal-entries` - List journal entries
- `POST /financial/journal-entries` - Create journal entry
- `GET /financial/ledger/<id>` - Account ledger
- `GET /financial/trial-balance` - Trial balance report
- `GET /financial/income-statement` - P&L statement
- `GET /financial/balance-sheet` - Balance sheet

### Reporting
- `GET /reporting/dashboard` - Dashboard KPIs
- `GET /reporting/inventory-report` - Inventory report
- `GET /reporting/sales-report` - Sales report
- `GET /reporting/financial-summary` - Financial summary

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
project/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py             # Configuration
│   ├── models/               # SQLAlchemy models
│   └── modules/              # Feature modules
│       ├── auth.py
│       ├── procurement.py
│       ├── goods_receiving.py
│       ├── production.py
│       ├── packaging.py
│       ├── sales.py
│       ├── financial.py
│       └── reporting.py
├── tests/                    # Test files
├── run.py                    # Application entry point
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## License

MIT