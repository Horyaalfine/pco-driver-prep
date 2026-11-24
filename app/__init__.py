from flask import Flask

from config import Config
from app.extensions import db, migrate, login_manager, mail


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth import auth_bp
    from app.learning import learning_bp
    from app.billing import billing_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(billing_bp, url_prefix="/billing")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_globals():
        return {"app_name": app.config["APP_NAME"]}

    return app
