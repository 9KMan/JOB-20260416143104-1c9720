from flask import Blueprint, request, jsonify
from app import db
from app.models import Account, JournalEntry, JournalEntryLine, Invoice, Payment
from datetime import datetime
from decimal import Decimal

financial_bp = Blueprint('financial', __name__)

def generate_entry_number():
    last_entry = JournalEntry.query.order_by(JournalEntry.id.desc()).first()
    if last_entry and last_entry.entry_number:
        num = int(last_entry.entry_number.replace('JE-', '')) + 1
        return f'JE-{num:06d}'
    return 'JE-000001'

def init_default_accounts():
    if Account.query.count() == 0:
        accounts = [
            Account(code='1000', name='Cash', account_type='asset'),
            Account(code='1100', name='Accounts Receivable', account_type='asset'),
            Account(code='1200', name='Inventory', account_type='asset'),
            Account(code='1500', name='Equipment', account_type='asset'),
            Account(code='2000', name='Accounts Payable', account_type='liability'),
            Account(code='2100', name='Notes Payable', account_type='liability'),
            Account(code='2500', name='Taxes Payable', account_type='liability'),
            Account(code='3000', name='Common Stock', account_type='equity'),
            Account(code='3100', name='Retained Earnings', account_type='equity'),
            Account(code='4000', name='Sales Revenue', account_type='revenue'),
            Account(code='4100', name='Service Revenue', account_type='revenue'),
            Account(code='5000', name='Cost of Goods Sold', account_type='expense'),
            Account(code='5100', name='Salaries Expense', account_type='expense'),
            Account(code='5200', name='Rent Expense', account_type='expense'),
            Account(code='5300', name='Utilities Expense', account_type='expense'),
            Account(code='5400', name='Depreciation Expense', account_type='expense'),
        ]
        for acc in accounts:
            db.session.add(acc)
        db.session.commit()

@financial_bp.route('/accounts', methods=['GET'])
def get_accounts():
    init_default_accounts()
    accounts = Account.query.filter_by(is_active=True).order_by(Account.code).all()
    return jsonify([{'id': a.id, 'code': a.code, 'name': a.name, 'account_type': a.account_type,
                     'description': a.description} for a in accounts])

@financial_bp.route('/accounts', methods=['POST'])
def create_account():
    data = request.get_json()
    account = Account(code=data['code'], name=data['name'], account_type=data['account_type'],
                      description=data.get('description'))
    db.session.add(account)
    db.session.commit()
    return jsonify({'id': account.id, 'message': 'Account created'}), 201

@financial_bp.route('/accounts/<int:id>', methods=['GET'])
def get_account(id):
    account = Account.query.get_or_404(id)
    return jsonify({'id': account.id, 'code': account.code, 'name': account.name,
                    'account_type': account.account_type, 'description': account.description})

@financial_bp.route('/journal-entries', methods=['GET'])
def get_journal_entries():
    entries = JournalEntry.query.order_by(JournalEntry.entry_date.desc()).all()
    return jsonify([{'id': e.id, 'entry_number': e.entry_number, 'entry_date': e.entry_date.isoformat() if e.entry_date else None,
                     'description': e.description, 'reference': e.reference, 'status': e.status} for e in entries])

@financial_bp.route('/journal-entries', methods=['POST'])
def create_journal_entry():
    data = request.get_json()
    entry = JournalEntry(entry_number=generate_entry_number(), description=data.get('description'),
                          reference=data.get('reference'), status='posted')
    if data.get('entry_date'):
        entry.entry_date = datetime.strptime(data['entry_date'], '%Y-%m-%d').date()
    db.session.add(entry)
    db.session.flush()

    for line in data.get('lines', []):
        je_line = JournalEntryLine(journal_entry_id=entry.id, account_id=line['account_id'],
                                    debit=Decimal(str(line.get('debit', 0))),
                                    credit=Decimal(str(line.get('credit', 0))))
        db.session.add(je_line)
    db.session.commit()
    return jsonify({'id': entry.id, 'entry_number': entry.entry_number, 'message': 'Journal entry created'}), 201

@financial_bp.route('/journal-entries/<int:id>', methods=['GET'])
def get_journal_entry(id):
    entry = JournalEntry.query.get_or_404(id)
    lines = [{'id': l.id, 'account_id': l.account_id, 'account_name': l.account.name if l.account else None,
              'account_code': l.account.code if l.account else None,
              'debit': float(l.debit), 'credit': float(l.credit)} for l in entry.lines]
    return jsonify({'id': entry.id, 'entry_number': entry.entry_number,
                    'entry_date': entry.entry_date.isoformat() if entry.entry_date else None,
                    'description': entry.description, 'reference': entry.reference, 'status': entry.status, 'lines': lines})

@financial_bp.route('/ledger/<int:account_id>', methods=['GET'])
def get_ledger(account_id):
    account = Account.query.get_or_404(account_id)
    lines = JournalEntryLine.query.filter_by(account_id=account_id).order_by(JournalEntryLine.created_at).all()
    balance = Decimal('0')
    entries = []
    for line in lines:
        if account.account_type in ['asset', 'expense']:
            balance += line.debit - line.credit
        else:
            balance += line.credit - line.debit
        entries.append({'date': line.created_at.isoformat(), 'description': line.journal_entry.description,
                         'debit': float(line.debit), 'credit': float(line.credit), 'balance': float(balance)})
    return jsonify({'account': {'id': account.id, 'code': account.code, 'name': account.name},
                    'entries': entries, 'current_balance': float(balance)})

@financial_bp.route('/trial-balance', methods=['GET'])
def get_trial_balance():
    init_default_accounts()
    accounts = Account.query.filter_by(is_active=True).order_by(Account.code).all()
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    balances = []
    for acc in accounts:
        debit = sum(l.debit for l in acc.entries)
        credit = sum(l.credit for l in acc.entries)
        if acc.account_type in ['asset', 'expense']:
            balance = debit - credit
            total_debit += balance
        else:
            balance = credit - debit
            total_credit += balance
        balances.append({'account_id': acc.id, 'account_code': acc.code, 'account_name': acc.name,
                         'account_type': acc.account_type, 'debit': float(debit), 'credit': float(credit),
                         'balance': float(balance)})
    return jsonify({'accounts': balances, 'total_debit': float(total_debit), 'total_credit': float(total_credit),
                    'is_balanced': total_debit == total_credit})

@financial_bp.route('/income-statement', methods=['GET'])
def get_income_statement():
    revenues = Account.query.filter_by(account_type='revenue').all()
    expenses = Account.query.filter_by(account_type='expense').all()
    total_revenue = sum(sum(l.debit - l.credit for l in a.entries) for a in revenues)
    total_expense = sum(sum(l.credit - l.debit for l in a.entries) for a in expenses)
    return jsonify({'revenues': [{'name': r.name, 'code': r.code, 'amount': float(sum(l.debit - l.credit for l in r.entries))} for r in revenues],
                    'expenses': [{'name': e.name, 'code': e.code, 'amount': float(sum(l.credit - l.debit for l in e.entries))} for e in expenses],
                    'total_revenue': float(total_revenue), 'total_expense': float(total_expense),
                    'net_income': float(total_revenue - total_expense)})

@financial_bp.route('/balance-sheet', methods=['GET'])
def get_balance_sheet():
    assets = Account.query.filter_by(account_type='asset').all()
    liabilities = Account.query.filter_by(account_type='liability').all()
    equity = Account.query.filter_by(account_type='equity').all()
    total_assets = sum(sum(l.debit - l.credit for l in a.entries) for a in assets)
    total_liabilities = sum(sum(l.credit - l.debit for l in a.entries) for a in liabilities)
    revenues = sum(sum(l.debit - l.credit for l in a.entries) for a in Account.query.filter_by(account_type='revenue').all())
    expenses = sum(sum(l.credit - l.debit for l in a.entries) for a in Account.query.filter_by(account_type='expense').all())
    retained_earnings = revenues - expenses
    total_equity = sum(sum(l.credit - l.debit for l in a.entries) for a in equity) + retained_earnings
    return jsonify({
        'assets': [{'name': a.name, 'code': a.code, 'amount': float(sum(l.debit - l.credit for l in a.entries))} for a in assets],
        'liabilities': [{'name': l.name, 'code': l.code, 'amount': float(sum(l.credit - l.debit for l in l.entries))} for l in liabilities],
        'equity': [{'name': e.name, 'code': e.code, 'amount': float(sum(l.credit - l.debit for l in e.entries))} for e in equity] + [{'name': 'Retained Earnings', 'amount': float(retained_earnings)}],
        'total_assets': float(total_assets), 'total_liabilities': float(total_liabilities),
        'total_equity': float(total_equity), 'is_balanced': abs(total_assets - total_liabilities - total_equity) < 0.01
    })