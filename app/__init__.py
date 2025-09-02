from flask import Flask, g, jsonify, render_template
from .routes import register_routes
from .models.database import close_db_connection, init_db_pool
import firebase_admin
from firebase_admin import credentials
import os

def create_app(config=None):
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        from config import Config
        app.config.from_object(Config)
    
    # Initialize database connection pool
    with app.app_context():
        init_db_pool()
    
    # Initialize Firebase
    if not firebase_admin._apps:
        try:
            if os.path.exists(app.config['FIREBASE_KEY_PATH']):
                cred = credentials.Certificate(app.config['FIREBASE_KEY_PATH'])
                firebase_admin.initialize_app(cred)
            else:
                print(f"Warning: Firebase key file not found at {app.config['FIREBASE_KEY_PATH']}")
        except Exception as e:
            print(f"Firebase initialization error: {e}")
    
    # Register error handlers
    @app.errorhandler(500)
    def internal_error(error):
        message = "An internal server error occurred. Please try again later"
        if os.getenv("FLASK_ENV") == "development":
            message += " " + str(error)
        return jsonify({"error": message}), 500
    
    @app.teardown_request
    def teardown_request(exception):
        close_db_connection(exception)
    
    # Register routes
    register_routes(app)
    
    # Basic index route
    @app.route("/")
    def index():
        return {"message": "Pixel Weather API", "status": "running"}
    
    return app