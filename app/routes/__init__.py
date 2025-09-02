from .auth_routes import auth_bp
from .user_routes import user_bp
from .post_routes import post_bp
from .data_routes import data_bp
from .notification_routes import notification_bp
from .user_data_routes import user_data_bp
from .health_routes import health_bp

def register_routes(app):
    """Register all route blueprints"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(post_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(user_data_bp)
    app.register_blueprint(health_bp)