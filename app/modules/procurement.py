from flask import Blueprint, request, jsonify
from app import db
from app.models import Supplier, PurchaseOrder, PurchaseOrderItem, Product
from datetime import datetime
from decimal import Decimal

procurement_bp = Blueprint('procurement', __name__)

def generate_po_number():
    last_po = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
    if last_po and last_po.po_number:
        num = int(last_po.po_number.replace('PO-', '')) + 1
        return f'PO-{num:06d}'
    return 'PO-000001'

@procurement_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return jsonify([{'id': s.id, 'name': s.name, 'contact_person': s.contact_person,
                     'email': s.email, 'phone': s.phone, 'address': s.address} for s in suppliers])

@procurement_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    data = request.get_json()
    supplier = Supplier(name=data['name'], contact_person=data.get('contact_person'),
                        email=data.get('email'), phone=data.get('phone'), address=data.get('address'))
    db.session.add(supplier)
    db.session.commit()
    return jsonify({'id': supplier.id, 'message': 'Supplier created'}), 201

@procurement_bp.route('/suppliers/<int:id>', methods=['GET'])
def get_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    return jsonify({'id': supplier.id, 'name': supplier.name, 'contact_person': supplier.contact_person,
                    'email': supplier.email, 'phone': supplier.phone, 'address': supplier.address})

@procurement_bp.route('/suppliers/<int:id>', methods=['PUT'])
def update_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    data = request.get_json()
    supplier.name = data.get('name', supplier.name)
    supplier.contact_person = data.get('contact_person', supplier.contact_person)
    supplier.email = data.get('email', supplier.email)
    supplier.phone = data.get('phone', supplier.phone)
    supplier.address = data.get('address', supplier.address)
    db.session.commit()
    return jsonify({'message': 'Supplier updated'})

@procurement_bp.route('/suppliers/<int:id>', methods=['DELETE'])
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    supplier.is_active = False
    db.session.commit()
    return jsonify({'message': 'Supplier deactivated'})

@procurement_bp.route('/purchase-orders', methods=['GET'])
def get_purchase_orders():
    orders = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    return jsonify([{'id': o.id, 'po_number': o.po_number, 'supplier_id': o.supplier_id,
                     'supplier_name': o.supplier.name if o.supplier else None,
                     'order_date': o.order_date.isoformat() if o.order_date else None,
                     'expected_delivery_date': o.expected_delivery_date.isoformat() if o.expected_delivery_date else None,
                     'status': o.status, 'total_amount': float(o.total_amount)} for o in orders])

@procurement_bp.route('/purchase-orders', methods=['POST'])
def create_purchase_order():
    data = request.get_json()
    po = PurchaseOrder(po_number=generate_po_number(), supplier_id=data['supplier_id'],
                      order_date=datetime.strptime(data['order_date'], '%Y-%m-%d').date() if data.get('order_date') else datetime.utcnow().date(),
                      expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() if data.get('expected_delivery_date') else None,
                      notes=data.get('notes'), status='pending')
    db.session.add(po)
    db.session.flush()

    total = Decimal('0')
    for item in data.get('items', []):
        po_item = PurchaseOrderItem(purchase_order_id=po.id, product_id=item['product_id'],
                                     quantity=item['quantity'], unit_price=Decimal(str(item['unit_price'])))
        db.session.add(po_item)
        total += Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))

    po.total_amount = total
    db.session.commit()
    return jsonify({'id': po.id, 'po_number': po.po_number, 'message': 'Purchase order created'}), 201

@procurement_bp.route('/purchase-orders/<int:id>', methods=['GET'])
def get_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    items = [{'id': i.id, 'product_id': i.product_id, 'product_name': i.product.name if i.product else None,
              'quantity': i.quantity, 'unit_price': float(i.unit_price), 'received_quantity': i.received_quantity} for i in po.items]
    return jsonify({'id': po.id, 'po_number': po.po_number, 'supplier_id': po.supplier_id,
                    'supplier_name': po.supplier.name if po.supplier else None,
                    'order_date': po.order_date.isoformat() if po.order_date else None,
                    'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
                    'status': po.status, 'total_amount': float(po.total_amount), 'items': items})

@procurement_bp.route('/purchase-orders/<int:id>', methods=['PUT'])
def update_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    data = request.get_json()
    po.status = data.get('status', po.status)
    po.notes = data.get('notes', po.notes)
    db.session.commit()
    return jsonify({'message': 'Purchase order updated'})

@procurement_bp.route('/purchase-orders/<int:id>/cancel', methods=['POST'])
def cancel_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    if po.status in ['received', 'closed']:
        return jsonify({'error': 'Cannot cancel received or closed orders'}), 400
    po.status = 'cancelled'
    db.session.commit()
    return jsonify({'message': 'Purchase order cancelled'})

@procurement_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([{'id': p.id, 'sku': p.sku, 'name': p.name, 'description': p.description,
                     'unit_price': float(p.unit_price), 'unit_cost': float(p.unit_cost),
                     'quantity_on_hand': p.quantity_on_hand, 'reorder_level': p.reorder_level} for p in products])

@procurement_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    product = Product(sku=data['sku'], name=data['name'], description=data.get('description'),
                      unit_price=Decimal(str(data.get('unit_price', 0))), unit_cost=Decimal(str(data.get('unit_cost', 0))),
                      quantity_on_hand=data.get('quantity_on_hand', 0), reorder_level=data.get('reorder_level', 10))
    db.session.add(product)
    db.session.commit()
    return jsonify({'id': product.id, 'message': 'Product created'}), 201

@procurement_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({'id': product.id, 'sku': product.sku, 'name': product.name,
                    'description': product.description, 'unit_price': float(product.unit_price),
                    'unit_cost': float(product.unit_cost), 'quantity_on_hand': product.quantity_on_hand,
                    'reorder_level': product.reorder_level})

@procurement_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.unit_price = Decimal(str(data.get('unit_price', product.unit_price)))
    product.unit_cost = Decimal(str(data.get('unit_cost', product.unit_cost)))
    product.quantity_on_hand = data.get('quantity_on_hand', product.quantity_on_hand)
    product.reorder_level = data.get('reorder_level', product.reorder_level)
    db.session.commit()
    return jsonify({'message': 'Product updated'})