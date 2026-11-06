from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import Forbidden
from werkzeug.middleware.proxy_fix import ProxyFix

from app.blueprints.auth import auth_bp
from app.blueprints.health import health_bp
from app.blueprints.pages import pages_bp
from app.config import apply_environment, load_local_env, resolve_config
from app.extensions import csrf, db, limiter, login_manager, migrate
from app.logging_config import configure_logging
from app.security import register_security_headers


def create_app(config_class=None):
    app = Flask(__name__, instance_relative_config=True)
    if config_class is None:
        load_local_env()
        config_class = resolve_config()
    app.config.from_object(config_class)
    apply_environment(app, config_class)
    selected = config_class
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    if app.config.get("TRUST_PROXY"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    configure_logging(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    register_security_headers(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    _register_error_handlers(app)
    app.logger.info("application started config=%s", selected.__name__)
    return app


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify(error="not_found"), 404
        return render_template("not_found.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        app.logger.exception("unhandled server error")
        return jsonify(error="server_error"), 500

    @app.errorhandler(429)
    def rate_limited(_error):
        return jsonify(error="rate_limited"), 429

    @app.errorhandler(Forbidden)
    def forbidden(_error):
        if request.path.startswith("/api/"):
            return jsonify(error="forbidden"), 403
        return render_template("forbidden.html"), 403

    @app.errorhandler(CSRFError)
    def csrf_failed(error):
        app.logger.info("csrf rejected path=%s reason=%s", request.path, error.description)
        if request.path.startswith("/api/"):
            return jsonify(error="csrf_failed"), 400
        return render_template("csrf_error.html"), 400
