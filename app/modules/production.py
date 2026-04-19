from flask import Blueprint, request, jsonify
from app import db
from app.models import WorkOrder, WorkOrderItem, Product
from datetime import datetime
from decimal import Decimal

production_bp = Blueprint('production', __name__)

def generate_wo_number():
    last_wo = WorkOrder.query.order_by(WorkOrder.id.desc()).first()
    if last_wo and last_wo.wo_number:
        num = int(last_wo.wo_number.replace('WO-', '')) + 1
        return f'WO-{num:06d}'
    return 'WO-000001'

@production_bp.route('/work-orders', methods=['GET'])
def get_work_orders():
    orders = WorkOrder.query.order_by(WorkOrder.created_at.desc()).all()
    return jsonify([{'id': o.id, 'wo_number': o.wo_number, 'product_id': o.product_id,
                     'product_name': o.product.name if o.product else None,
                     'quantity': o.quantity, 'scheduled_start_date': o.scheduled_start_date.isoformat() if o.scheduled_start_date else None,
                     'scheduled_end_date': o.scheduled_end_date.isoformat() if o.scheduled_end_date else None,
                     'status': o.status} for o in orders])

@production_bp.route('/work-orders', methods=['POST'])
def create_work_order():
    data = request.get_json()
    wo = WorkOrder(wo_number=generate_wo_number(), product_id=data['product_id'], quantity=data['quantity'],
                   scheduled_start_date=datetime.strptime(data['scheduled_start_date'], '%Y-%m-%d').date() if data.get('scheduled_start_date') else None,
                   scheduled_end_date=datetime.strptime(data['scheduled_end_date'], '%Y-%m-%d').date() if data.get('scheduled_end_date') else None,
                   notes=data.get('notes'), status='pending')
    db.session.add(wo)
    db.session.flush()

    for item in data.get('items', []):
        wo_item = WorkOrderItem(work_order_id=wo.id, product_id=item['product_id'],
                                 quantity_required=item['quantity_required'])
        db.session.add(wo_item)
    db.session.commit()
    return jsonify({'id': wo.id, 'wo_number': wo.wo_number, 'message': 'Work order created'}), 201

@production_bp.route('/work-orders/<int:id>', methods=['GET'])
def get_work_order(id):
    wo = WorkOrder.query.get_or_404(id)
    items = [{'id': i.id, 'product_id': i.product_id, 'product_name': i.product.name if i.product else None,
              'quantity_required': i.quantity_required, 'quantity_used': i.quantity_used} for i in wo.items]
    return jsonify({'id': wo.id, 'wo_number': wo.wo_number, 'product_id': wo.product_id,
                    'product_name': wo.product.name if wo.product else None, 'quantity': wo.quantity,
                    'scheduled_start_date': wo.scheduled_start_date.isoformat() if wo.scheduled_start_date else None,
                    'scheduled_end_date': wo.scheduled_end_date.isoformat() if wo.scheduled_end_date else None,
                    'actual_start_date': wo.actual_start_date.isoformat() if wo.actual_start_date else None,
                    'actual_end_date': wo.actual_end_date.isoformat() if wo.actual_end_date else None,
                    'status': wo.status, 'notes': wo.notes, 'items': items})

@production_bp.route('/work-orders/<int:id>', methods=['PUT'])
def update_work_order(id):
    wo = WorkOrder.query.get_or_404(id)
    data = request.get_json()
    wo.status = data.get('status', wo.status)
    wo.notes = data.get('notes', wo.notes)
    if data.get('actual_start_date'):
        wo.actual_start_date = datetime.strptime(data['actual_start_date'], '%Y-%m-%d').date()
    if data.get('actual_end_date'):
        wo.actual_end_date = datetime.strptime(data['actual_end_date'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'message': 'Work order updated'})

@production_bp.route('/work-orders/<int:id>/start', methods=['POST'])
def start_work_order(id):
    wo = WorkOrder.query.get_or_404(id)
    if wo.status != 'pending':
        return jsonify({'error': 'Can only start pending work orders'}), 400
    wo.status = 'in_progress'
    wo.actual_start_date = datetime.utcnow().date()
    db.session.commit()
    return jsonify({'message': 'Work order started'})

@production_bp.route('/work-orders/<int:id>/complete', methods=['POST'])
def complete_work_order(id):
    wo = WorkOrder.query.get_or_404(id)
    if wo.status != 'in_progress':
        return jsonify({'error': 'Can only complete work orders in progress'}), 400
    wo.status = 'completed'
    wo.actual_end_date = datetime.utcnow().date()
    product = Product.query.get(wo.product_id)
    if product:
        product.quantity_on_hand += wo.quantity
    db.session.commit()
    return jsonify({'message': 'Work order completed'})

@production_bp.route('/work-orders/<int:id>/cancel', methods=['POST'])
def cancel_work_order(id):
    wo = WorkOrder.query.get_or_404(id)
    if wo.status == 'completed':
        return jsonify({'error': 'Cannot cancel completed work orders'}), 400
    wo.status = 'cancelled'
    db.session.commit()
    return jsonify({'message': 'Work order cancelled'})