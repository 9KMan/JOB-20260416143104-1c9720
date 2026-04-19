import pytest
from app import create_app, db
from app.models import User, Supplier, Customer, Product, Account

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_index_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'ERP System API' in response.json['message']

def test_user_registration(client):
    response = client.post('/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'

def test_user_login(client, app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()

    response = client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    assert response.json['message'] == 'Login successful'

def test_create_supplier(client):
    response = client.post('/procurement/suppliers', json={
        'name': 'Test Supplier',
        'contact_person': 'John Doe',
        'email': 'supplier@test.com',
        'phone': '+1234567890'
    })
    assert response.status_code == 201
    assert response.json['message'] == 'Supplier created'

def test_get_suppliers(client):
    client.post('/procurement/suppliers', json={'name': 'Supplier 1', 'email': 's1@test.com'})
    client.post('/procurement/suppliers', json={'name': 'Supplier 2', 'email': 's2@test.com'})
    response = client.get('/procurement/suppliers')
    assert response.status_code == 200
    assert len(response.json) == 2

def test_create_product(client):
    response = client.post('/procurement/products', json={
        'sku': 'PROD-001',
        'name': 'Test Product',
        'unit_price': 99.99,
        'unit_cost': 49.99
    })
    assert response.status_code == 201
    assert response.json['message'] == 'Product created'

def test_create_customer(client):
    response = client.post('/sales/customers', json={
        'name': 'Test Customer',
        'contact_person': 'Jane Doe',
        'email': 'customer@test.com'
    })
    assert response.status_code == 201
    assert response.json['message'] == 'Customer created'

def test_get_customers(client):
    client.post('/sales/customers', json={'name': 'Customer 1', 'email': 'c1@test.com'})
    response = client.get('/sales/customers')
    assert response.status_code == 200
    assert len(response.json) >= 1

def test_accounts_endpoint(client):
    response = client.get('/financial/accounts')
    assert response.status_code == 200

def test_trial_balance(client):
    response = client.get('/financial/trial-balance')
    assert response.status_code == 200
    assert 'accounts' in response.json
    assert 'total_debit' in response.json
    assert 'total_credit' in response.json

def test_dashboard(client):
    response = client.get('/reporting/dashboard')
    assert response.status_code == 200
    assert 'total_products' in response.json
    assert 'pending_purchase_orders' in response.json

def test_inventory_report(client):
    response = client.get('/reporting/inventory-report')
    assert response.status_code == 200