from flask import Blueprint, request, jsonify
from app import db
from app.models import Product, PurchaseOrder, SalesOrder, Invoice, Payment, WorkOrder, GoodsReceipt
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime, timedelta

reporting_bp = Blueprint('reporting', __name__)

@reporting_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    total_products = Product.query.filter_by(is_active=True).count()
    total_customers = db.session.query(func.count(db.func.distinct(db.column('id')))).select_from(db.text('customers')).scalar()
    total_suppliers = db.session.query(func.count(db.func.distinct(db.text('id')))).select_from(db.text('suppliers')).scalar()

    pending_po = PurchaseOrder.query.filter_by(status='pending').count()
    pending_so = SalesOrder.query.filter_by(status='pending').count()
    active_wo = WorkOrder.query.filter(WorkOrder.status.in_(['pending', 'in_progress'])).count()

    low_stock = Product.query.filter(Product.quantity_on_hand <= Product.reorder_level, Product.is_active == True).count()

    monthly_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.status == 'paid',
        Invoice.invoice_date >= datetime.utcnow().date().replace(day=1)
    ).scalar() or Decimal('0')

    monthly_sales = db.session.query(func.count(Invoice.id)).filter(
        Invoice.invoice_date >= datetime.utcnow().date().replace(day=1)
    ).scalar() or 0

    return jsonify({
        'total_products': total_products,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
        'pending_purchase_orders': pending_po,
        'pending_sales_orders': pending_so,
        'active_work_orders': active_wo,
        'low_stock_items': low_stock,
        'monthly_revenue': float(monthly_revenue),
        'monthly_sales_count': monthly_sales
    })

@reporting_bp.route('/inventory-report', methods=['GET'])
def get_inventory_report():
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([{'sku': p.sku, 'name': p.name, 'quantity_on_hand': p.quantity_on_hand,
                     'reorder_level': p.reorder_level, 'unit_cost': float(p.unit_cost),
                     'unit_price': float(p.unit_price), 'inventory_value': float(p.quantity_on_hand * p.unit_cost),
                     'status': 'Low Stock' if p.quantity_on_hand <= p.reorder_level else 'In Stock'} for p in products])

@reporting_bp.route('/sales-report', methods=['GET'])
def get_sales_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query = db.session.query(SalesOrder)
    if start_date:
        query = query.filter(SalesOrder.order_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(SalesOrder.order_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    orders = query.all()
    total_amount = sum(float(o.total_amount) for o in orders)
    return jsonify({'orders': [{'order_number': o.order_number, 'customer': o.customer.name if o.customer else None,
                                'order_date': o.order_date.isoformat() if o.order_date else None,
                                'status': o.status, 'total_amount': float(o.total_amount)} for o in orders],
                    'total_orders': len(orders), 'total_amount': total_amount})

@reporting_bp.route('/financial-summary', methods=['GET'])
def get_financial_summary():
    total_receivables = db.session.query(func.sum(Invoice.total_amount - Invoice.amount_paid)).filter(
        Invoice.status != 'paid'
    ).scalar() or Decimal('0')

    total_payables = db.session.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.status == 'pending'
    ).scalar() or Decimal('0')

    monthly_income = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.status == 'paid',
        Invoice.invoice_date >= datetime.utcnow().date().replace(day=1)
    ).scalar() or Decimal('0')

    return jsonify({
        'total_receivables': float(total_receivables),
        'total_payables': float(total_payables),
        'monthly_income': float(monthly_income),
        'report_date': datetime.utcnow().isoformat()
    })

@reporting_bp.route('/production-report', methods=['GET'])
def get_production_report():
    work_orders = WorkOrder.query.all()
    return jsonify([{'wo_number': wo.wo_number, 'product': wo.product.name if wo.product else None,
                     'quantity': wo.quantity, 'scheduled_start': wo.scheduled_start_date.isoformat() if wo.scheduled_start_date else None,
                     'scheduled_end': wo.scheduled_end_date.isoformat() if wo.scheduled_end_date else None,
                     'actual_start': wo.actual_start_date.isoformat() if wo.actual_start_date else None,
                     'actual_end': wo.actual_end_date.isoformat() if wo.actual_end_date else None,
                     'status': wo.status} for wo in work_orders])}