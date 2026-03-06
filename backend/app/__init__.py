from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

from app.data_paths import configure_data_environment

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    configure_data_environment()

    # Load config
    app.config.from_object("app.config.Config")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}}, supports_credentials=True, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.career import career_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.main import main_bp
    from app.routes.market import market_bp
    from app.routes.scraper import scraper_bp

    app.register_blueprint(main_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(career_bp, url_prefix="/api/career")
    app.register_blueprint(market_bp, url_prefix="/api/market")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(scraper_bp, url_prefix="/api/scraper")

    # Create database tables
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
