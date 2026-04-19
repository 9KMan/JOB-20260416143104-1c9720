from flask import Blueprint, request, jsonify
from app import db
from app.models import PackagingOrder, WorkOrder, SalesOrder
from datetime import datetime

packaging_bp = Blueprint('packaging', __name__)

def generate_packaging_number():
    last_po = PackagingOrder.query.order_by(PackagingOrder.id.desc()).first()
    if last_po and last_po.po_number:
        num = int(last_po.po_number.replace('PKG-', '')) + 1
        return f'PKG-{num:06d}'
    return 'PKG-000001'

@packaging_bp.route('/packaging-orders', methods=['GET'])
def get_packaging_orders():
    orders = PackagingOrder.query.order_by(PackagingOrder.created_at.desc()).all()
    return jsonify([{'id': o.id, 'po_number': o.po_number, 'work_order_id': o.work_order_id,
                     'wo_number': o.work_order.wo_number if o.work_order else None,
                     'sales_order_id': o.sales_order_id, 'sales_order_number': o.sales_order_no.order_number if o.sales_order_no else None,
                     'quantity': o.quantity, 'packaging_type': o.packaging_type,
                     'scheduled_date': o.scheduled_date.isoformat() if o.scheduled_date else None,
                     'status': o.status} for o in orders])

@packaging_bp.route('/packaging-orders', methods=['POST'])
def create_packaging_order():
    data = request.get_json()
    po = PackagingOrder(po_number=generate_packaging_number(), work_order_id=data.get('work_order_id'),
                         sales_order_id=data.get('sales_order_id'), quantity=data['quantity'],
                         packaging_type=data.get('packaging_type'), label_data=data.get('label_data'),
                         scheduled_date=datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date() if data.get('scheduled_date') else None,
                         notes=data.get('notes'), status='pending')
    db.session.add(po)
    db.session.commit()
    return jsonify({'id': po.id, 'po_number': po.po_number, 'message': 'Packaging order created'}), 201

@packaging_bp.route('/packaging-orders/<int:id>', methods=['GET'])
def get_packaging_order(id):
    po = PackagingOrder.query.get_or_404(id)
    return jsonify({'id': po.id, 'po_number': po.po_number, 'work_order_id': po.work_order_id,
                    'wo_number': po.work_order.wo_number if po.work_order else None,
                    'sales_order_id': po.sales_order_id, 'sales_order_number': po.sales_order_no.order_number if po.sales_order_no else None,
                    'quantity': po.quantity, 'packaging_type': po.packaging_type,
                    'label_data': po.label_data, 'scheduled_date': po.scheduled_date.isoformat() if po.scheduled_date else None,
                    'completed_date': po.completed_date.isoformat() if po.completed_date else None,
                    'status': po.status, 'notes': po.notes})

@packaging_bp.route('/packaging-orders/<int:id>', methods=['PUT'])
def update_packaging_order(id):
    po = PackagingOrder.query.get_or_404(id)
    data = request.get_json()
    po.status = data.get('status', po.status)
    po.notes = data.get('notes', po.notes)
    if data.get('packaging_type'):
        po.packaging_type = data['packaging_type']
    if data.get('label_data'):
        po.label_data = data['label_data']
    db.session.commit()
    return jsonify({'message': 'Packaging order updated'})

@packaging_bp.route('/packaging-orders/<int:id>/complete', methods=['POST'])
def complete_packaging_order(id):
    po = PackagingOrder.query.get_or_404(id)
    if po.status != 'in_progress':
        return jsonify({'error': 'Can only complete packaging orders in progress'}), 400
    po.status = 'completed'
    po.completed_date = datetime.utcnow().date()
    db.session.commit()
    return jsonify({'message': 'Packaging order completed'})

@packaging_bp.route('/packaging-orders/<int:id>/labels', methods=['GET'])
def get_labels(id):
    po = PackagingOrder.query.get_or_404(id)
    return jsonify({'po_number': po.po_number, 'packaging_type': po.packaging_type,
                    'label_data': po.label_data, 'quantity': po.quantity})