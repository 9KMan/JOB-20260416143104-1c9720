from flask import Blueprint, request, jsonify
from app import db
from app.models import Customer, SalesOrder, SalesOrderItem, Invoice, Payment, Product
from datetime import datetime
from decimal import Decimal

sales_bp = Blueprint('sales', __name__)

def generate_order_number():
    last_so = SalesOrder.query.order_by(SalesOrder.id.desc()).first()
    if last_so and last_so.order_number:
        num = int(last_so.order_number.replace('SO-', '')) + 1
        return f'SO-{num:06d}'
    return 'SO-000001'

def generate_invoice_number():
    last_inv = Invoice.query.order_by(Invoice.id.desc()).first()
    if last_inv and last_inv.invoice_number:
        num = int(last_inv.invoice_number.replace('INV-', '')) + 1
        return f'INV-{num:06d}'
    return 'INV-000001'

def generate_payment_number():
    last_pay = Payment.query.order_by(Payment.id.desc()).first()
    if last_pay and last_pay.payment_number:
        num = int(last_pay.payment_number.replace('PAY-', '')) + 1
        return f'PAY-{num:06d}'
    return 'PAY-000001'

@sales_bp.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.filter_by(is_active=True).all()
    return jsonify([{'id': c.id, 'name': c.name, 'contact_person': c.contact_person,
                     'email': c.email, 'phone': c.phone, 'address': c.address} for c in customers])

@sales_bp.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    customer = Customer(name=data['name'], contact_person=data.get('contact_person'),
                         email=data.get('email'), phone=data.get('phone'), address=data.get('address'))
    db.session.add(customer)
    db.session.commit()
    return jsonify({'id': customer.id, 'message': 'Customer created'}), 201

@sales_bp.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    data = request.get_json()
    customer.name = data.get('name', customer.name)
    customer.contact_person = data.get('contact_person', customer.contact_person)
    customer.email = data.get('email', customer.email)
    customer.phone = data.get('phone', customer.phone)
    customer.address = data.get('address', customer.address)
    db.session.commit()
    return jsonify({'message': 'Customer updated'})

@sales_bp.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    customer.is_active = False
    db.session.commit()
    return jsonify({'message': 'Customer deactivated'})

@sales_bp.route('/sales-orders', methods=['GET'])
def get_sales_orders():
    orders = SalesOrder.query.order_by(SalesOrder.created_at.desc()).all()
    return jsonify([{'id': o.id, 'order_number': o.order_number, 'customer_id': o.customer_id,
                     'customer_name': o.customer.name if o.customer else None,
                     'order_date': o.order_date.isoformat() if o.order_date else None,
                     'delivery_date': o.delivery_date.isoformat() if o.delivery_date else None,
                     'status': o.status, 'total_amount': float(o.total_amount)} for o in orders])

@sales_bp.route('/sales-orders', methods=['POST'])
def create_sales_order():
    data = request.get_json()
    so = SalesOrder(order_number=generate_order_number(), customer_id=data['customer_id'],
                    order_date=datetime.strptime(data['order_date'], '%Y-%m-%d').date() if data.get('order_date') else datetime.utcnow().date(),
                    delivery_date=datetime.strptime(data['delivery_date'], '%Y-%m-%d').date() if data.get('delivery_date') else None,
                    discount_percent=Decimal(str(data.get('discount_percent', 0))), notes=data.get('notes'), status='pending')
    db.session.add(so)
    db.session.flush()

    subtotal = Decimal('0')
    for item in data.get('items', []):
        unit_price = Decimal(str(item['unit_price']))
        qty = Decimal(str(item['quantity']))
        discount = Decimal(str(item.get('discount_percent', 0)))
        line_total = unit_price * qty * (1 - discount / 100)
        so_item = SalesOrderItem(sales_order_id=so.id, product_id=item['product_id'],
                                  quantity=item['quantity'], unit_price=unit_price, discount_percent=discount)
        db.session.add(so_item)
        subtotal += line_total

    discount_amount = subtotal * so.discount_percent / 100
    so.total_amount = subtotal - discount_amount
    db.session.commit()
    return jsonify({'id': so.id, 'order_number': so.order_number, 'message': 'Sales order created'}), 201

@sales_bp.route('/sales-orders/<int:id>', methods=['GET'])
def get_sales_order(id):
    so = SalesOrder.query.get_or_404(id)
    items = [{'id': i.id, 'product_id': i.product_id, 'product_name': i.product.name if i.product else None,
              'quantity': i.quantity, 'unit_price': float(i.unit_price), 'discount_percent': float(i.discount_percent)} for i in so.items]
    return jsonify({'id': so.id, 'order_number': so.order_number, 'customer_id': so.customer_id,
                    'customer_name': so.customer.name if so.customer else None,
                    'order_date': so.order_date.isoformat() if so.order_date else None,
                    'delivery_date': so.delivery_date.isoformat() if so.delivery_date else None,
                    'status': so.status, 'total_amount': float(so.total_amount),
                    'discount_percent': float(so.discount_percent), 'items': items})

@sales_bp.route('/sales-orders/<int:id>', methods=['PUT'])
def update_sales_order(id):
    so = SalesOrder.query.get_or_404(id)
    data = request.get_json()
    so.status = data.get('status', so.status)
    so.notes = data.get('notes', so.notes)
    db.session.commit()
    return jsonify({'message': 'Sales order updated'})

@sales_bp.route('/sales-orders/<int:id>/invoice', methods=['POST'])
def create_invoice(id):
    so = SalesOrder.query.get_or_404(id)
    data = request.get_json()
    if so.status == 'invoiced':
        return jsonify({'error': 'Sales order already invoiced'}), 400
    tax_rate = Decimal(str(data.get('tax_rate', 10)))
    invoice = Invoice(invoice_number=generate_invoice_number(), sales_order_id=so.id,
                      due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None,
                      subtotal=so.total_amount, tax_amount=so.total_amount * tax_rate / 100,
                      total_amount=so.total_amount * (1 + tax_rate / 100), status='pending')
    db.session.add(invoice)
    so.status = 'invoiced'
    db.session.commit()
    return jsonify({'id': invoice.id, 'invoice_number': invoice.invoice_number, 'message': 'Invoice created'}), 201

@sales_bp.route('/invoices', methods=['GET'])
def get_invoices():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return jsonify([{'id': i.id, 'invoice_number': i.invoice_number, 'sales_order_id': i.sales_order_id,
                     'order_number': i.sales_order.order_number if i.sales_order else None,
                     'invoice_date': i.invoice_date.isoformat() if i.invoice_date else None,
                     'due_date': i.due_date.isoformat() if i.due_date else None,
                     'status': i.status, 'total_amount': float(i.total_amount),
                     'amount_paid': float(i.amount_paid)} for i in invoices])

@sales_bp.route('/invoices/<int:id>', methods=['GET'])
def get_invoice(id):
    inv = Invoice.query.get_or_404(id)
    return jsonify({'id': inv.id, 'invoice_number': inv.invoice_number, 'sales_order_id': inv.sales_order_id,
                    'order_number': inv.sales_order.order_number if inv.sales_order else None,
                    'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None,
                    'due_date': inv.due_date.isoformat() if inv.due_date else None,
                    'status': inv.status, 'subtotal': float(inv.subtotal), 'tax_amount': float(inv.tax_amount),
                    'total_amount': float(inv.total_amount), 'amount_paid': float(inv.amount_paid),
                    'notes': inv.notes})

@sales_bp.route('/invoices/<int:id>/payment', methods=['POST'])
def create_payment(id):
    inv = Invoice.query.get_or_404(id)
    data = request.get_json()
    payment = Payment(payment_number=generate_payment_number(), invoice_id=inv.id,
                      amount=Decimal(str(data['amount'])), payment_method=data.get('payment_method'),
                      reference=data.get('reference'), notes=data.get('notes'))
    db.session.add(payment)
    inv.amount_paid += payment.amount
    if inv.amount_paid >= inv.total_amount:
        inv.status = 'paid'
    db.session.commit()
    return jsonify({'id': payment.id, 'payment_number': payment.payment_number, 'message': 'Payment recorded'})