from flask import Blueprint, request, jsonify
from app import db
from app.models import GoodsReceipt, GoodsReceiptItem, PurchaseOrder, PurchaseOrderItem, Product, Warehouse
from datetime import datetime
from decimal import Decimal

goods_receiving_bp = Blueprint('goods_receiving', __name__)

def generate_grn_number():
    last_gr = GoodsReceipt.query.order_by(GoodsReceipt.id.desc()).first()
    if last_gr and last_gr.grn_number:
        num = int(last_gr.grn_number.replace('GRN-', '')) + 1
        return f'GRN-{num:06d}'
    return 'GRN-000001'

@goods_receiving_bp.route('/goods-receipts', methods=['GET'])
def get_goods_receipts():
    receipts = GoodsReceipt.query.order_by(GoodsReceipt.created_at.desc()).all()
    return jsonify([{'id': r.id, 'grn_number': r.grn_number, 'purchase_order_id': r.purchase_order_id,
                     'po_number': r.purchase_order.po_number if r.purchase_order else None,
                     'received_date': r.received_date.isoformat() if r.received_date else None,
                     'status': r.status, 'warehouse_name': r.warehouse.name if r.warehouse else None} for r in receipts])

@goods_receiving_bp.route('/goods-receipts', methods=['POST'])
def create_goods_receipt():
    data = request.get_json()
    gr = GoodsReceipt(grn_number=generate_grn_number(), purchase_order_id=data['purchase_order_id'],
                      received_date=datetime.strptime(data['received_date'], '%Y-%m-%d').date() if data.get('received_date') else datetime.utcnow().date(),
                      warehouse_id=data.get('warehouse_id'), status='received', notes=data.get('notes'))
    db.session.add(gr)
    db.session.flush()

    for item in data.get('items', []):
        gr_item = GoodsReceiptItem(goods_receipt_id=gr.id, product_id=item['product_id'],
                                    quantity_received=item['quantity_received'], quantity_inspected=item.get('quantity_inspected', item['quantity_received']),
                                    quantity_accepted=item.get('quantity_accepted', item['quantity_received']),
                                    quantity_rejected=item.get('quantity_rejected', 0), status='received')
        db.session.add(gr_item)
        product = Product.query.get(item['product_id'])
        if product:
            product.quantity_on_hand += item.get('quantity_accepted', item['quantity_received'])
        po_item = PurchaseOrderItem.query.filter_by(purchase_order_id=data['purchase_order_id'], product_id=item['product_id']).first()
        if po_item:
            po_item.received_quantity += item['quantity_received']

    db.session.commit()
    return jsonify({'id': gr.id, 'grn_number': gr.grn_number, 'message': 'Goods receipt created'}), 201

@goods_receiving_bp.route('/goods-receipts/<int:id>', methods=['GET'])
def get_goods_receipt(id):
    gr = GoodsReceipt.query.get_or_404(id)
    items = [{'id': i.id, 'product_id': i.product_id, 'product_name': i.product.name if i.product else None,
              'quantity_received': i.quantity_received, 'quantity_inspected': i.quantity_inspected,
              'quantity_accepted': i.quantity_accepted, 'quantity_rejected': i.quantity_rejected, 'status': i.status} for i in gr.items]
    return jsonify({'id': gr.id, 'grn_number': gr.grn_number, 'purchase_order_id': gr.purchase_order_id,
                    'po_number': gr.purchase_order.po_number if gr.purchase_order else None,
                    'received_date': gr.received_date.isoformat() if gr.received_date else None,
                    'status': gr.status, 'warehouse_id': gr.warehouse_id, 'warehouse_name': gr.warehouse.name if gr.warehouse else None,
                    'notes': gr.notes, 'items': items})

@goods_receiving_bp.route('/goods-receipts/<int:id>/inspect', methods=['POST'])
def inspect_goods_receipt(id):
    gr = GoodsReceipt.query.get_or_404(id)
    data = request.get_json()
    for item_data in data.get('items', []):
        item = GoodsReceiptItem.query.filter_by(goods_receipt_id=gr.id, product_id=item_data['product_id']).first()
        if item:
            item.quantity_inspected = item_data.get('quantity_inspected', item.quantity_inspected)
            item.quantity_accepted = item_data.get('quantity_accepted', item.quantity_accepted)
            item.quantity_rejected = item_data.get('quantity_rejected', item.quantity_rejected)
            item.status = 'inspected'
            product = Product.query.get(item.product_id)
            if product and item.quantity_accepted > item.quantity_received:
                product.quantity_on_hand += (item.quantity_accepted - item.quantity_received)
    gr.status = 'inspected'
    db.session.commit()
    return jsonify({'message': 'Goods receipt inspected'})

@goods_receiving_bp.route('/warehouses', methods=['GET'])
def get_warehouses():
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return jsonify([{'id': w.id, 'name': w.name, 'location': w.location} for w in warehouses])

@goods_receiving_bp.route('/warehouses', methods=['POST'])
def create_warehouse():
    data = request.get_json()
    warehouse = Warehouse(name=data['name'], location=data.get('location'))
    db.session.add(warehouse)
    db.session.commit()
    return jsonify({'id': warehouse.id, 'message': 'Warehouse created'}), 201