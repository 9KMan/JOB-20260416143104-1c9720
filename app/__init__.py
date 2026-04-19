from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from .config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    from app.modules.procurement import procurement_bp
    from app.modules.goods_receiving import goods_receiving_bp
    from app.modules.production import production_bp
    from app.modules.packaging import packaging_bp
    from app.modules.sales import sales_bp
    from app.modules.financial import financial_bp
    from app.modules.reporting import reporting_bp
    from app.modules.auth import auth_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(procurement_bp, url_prefix='/procurement')
    app.register_blueprint(goods_receiving_bp, url_prefix='/goods-receiving')
    app.register_blueprint(production_bp, url_prefix='/production')
    app.register_blueprint(packaging_bp, url_prefix='/packaging')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(financial_bp, url_prefix='/financial')
    app.register_blueprint(reporting_bp, url_prefix='/reporting')

    @app.route('/')
    def index():
        return {'message': 'ERP System API', 'version': '1.0.0'}

    @app.route('/health')
    def health():
        return {'status': 'healthy'}

    return app