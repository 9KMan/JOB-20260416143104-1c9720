import pytest
from app.models import User, Supplier, Product, Customer, PurchaseOrder

def test_user_password_hashing(app):
    with app.app_context():
        user = User(username='testuser', email='test@test.com')
        user.set_password('testpass')
        assert user.password_hash != 'testpass'
        assert user.check_password('testpass')
        assert not user.check_password('wrongpass')

def test_supplier_model(app):
    with app.app_context():
        supplier = Supplier(name='Test Supplier', email='test@supplier.com')
        db.session.add(supplier)
        db.session.commit()
        assert supplier.id is not None
        assert supplier.is_active is True

def test_product_model(app):
    with app.app_context():
        product = Product(sku='TEST-001', name='Test Product', unit_price=100, unit_cost=50)
        db.session.add(product)
        db.session.commit()
        assert product.id is not None
        assert product.quantity_on_hand == 0

def test_customer_model(app):
    with app.app_context():
        customer = Customer(name='Test Customer', email='test@customer.com')
        db.session.add(customer)
        db.session.commit()
        assert customer.id is not None
        assert customer.is_active is True

def test_purchase_order_creation(app):
    with app.app_context():
        supplier = Supplier(name='Test Supplier')
        db.session.add(supplier)
        db.session.flush()

        po = PurchaseOrder(po_number='PO-001', supplier_id=supplier.id)
        db.session.add(po)
        db.session.commit()
        assert po.id is not None
        assert po.status == 'pending'

from app import db