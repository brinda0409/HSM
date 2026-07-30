import os
from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

from services.db_service import init_db
from utils.logger import logger
from utils.error_handlers import register_error_handlers

from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.complaint_routes import complaint_bp
from routes.visitor_routes import visitor_bp
from routes.room_routes import room_bp
from routes.leave_routes import leave_bp
from routes.info_routes import info_bp
from routes.student_routes import student_bp
from routes.report_routes import report_bp

def create_app():
    """Factory function to configure and initialize Flask Application."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(base_dir, "templates")
    static_path = os.path.join(base_dir, "static")

    app = Flask(__name__, template_folder=templates_path, static_folder=static_path)
    app.secret_key = os.getenv("SECRET_KEY", "shms_secure_session_key_2026")

    # Safe Database Schema & Seed Data Initialization for Serverless Environments
    try:
        init_db()
    except Exception as e:
        logger.error(f"[App] Non-fatal database initialization warning: {e}")

    # Register Error Handlers
    register_error_handlers(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(visitor_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(info_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(report_bp)


    @app.route("/")
    @app.route("/api/index.py")
    def landing():
        """SaaS Product Landing Page"""
        return render_template("landing.html")

    @app.route("/login")
    def login_page():
        """SaaS Authentication & Dual-Role Login Page"""
        return render_template("login.html")

    @app.route("/app")
    @app.route("/portal")
    @app.route("/dashboard")
    @app.route("/warden")
    @app.route("/warden/dashboard")
    def app_portal():
        """Unified Platform SPA Engine for Authenticated Students & Wardens"""
        return render_template("index.html")

    return app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1", "t"]
    
    logger.info(f"Starting Smart Hostel Management System server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
# Server reloader trigger

