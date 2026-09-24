
import logging
import re

from flask import Flask, abort, render_template, request
from flask_login import current_user

from flask_migrate import Migrate

from .extensions import db, login_manager
from .config import Config

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def request_user_id():
    if current_user.is_authenticated:
        return current_user.id

    return "anonymous"


def create_app():

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.config.from_object(Config)

    app.logger.setLevel(app.config["LOG_LEVEL"])
    for handler in app.logger.handlers:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s"
            )
        )

    db.init_app(app)

    Migrate(
        app,
        db,
        compare_type=True,
        include_schemas=True
    )

    login_manager.init_app(app)

    @app.before_request
    def validate_request_input():
        for field, values in request.args.lists():
            for value in values:
                if len(value) > app.config["MAX_QUERY_VALUE_LENGTH"]:
                    app.logger.warning(
                        "Request parameter is too long: user_id=%s field=%s path=%s",
                        request_user_id(),
                        field,
                        request.path,
                    )
                    abort(400)

        for field, values in request.form.lists():
            max_length = app.config["INPUT_FIELD_LIMITS"].get(
                field,
                app.config["MAX_FORM_FIELD_LENGTH"],
            )
            for value in values:
                if len(value) > max_length:
                    app.logger.warning(
                        "Form field is too long: user_id=%s field=%s path=%s",
                        request_user_id(),
                        field,
                        request.path,
                    )
                    abort(400)

                if field == "email" and value and not EMAIL_PATTERN.fullmatch(value):
                    app.logger.warning(
                        "Invalid email format: user_id=%s path=%s",
                        request_user_id(),
                        request.path,
                    )
                    abort(400)

    @app.after_request
    def log_request(response):
        app.logger.info(
            "Request completed: user_id=%s method=%s path=%s status=%s",
            request_user_id(),
            request.method,
            request.path,
            response.status_code,
        )
        return response

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):

        return db.session.get(
            User,
            int(user_id)
        )

    from .admin_routes import register_admin_routes
    register_admin_routes(app)

    from .auth_routes import register_auth_routes
    register_auth_routes(app)

    from .submission_routes import register_submission_routes
    register_submission_routes(app)

    from .assignment_routes import register_assignment_routes
    register_assignment_routes(app)

    from .course_routes import register_course_routes
    register_course_routes(app)

    from .profile_routes import register_profile_routes
    register_profile_routes(app)

    @app.cli.command("create-test-users")
    def create_test_users_command():

        from .seed import create_test_users

        create_test_users()

    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning(
            "Access denied: method=%s path=%s",
            request.method,
            request.path,
        )
        return render_template("403.html"), 403

    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(
            "Invalid request: method=%s path=%s",
            request.method,
            request.path,
        )
        return render_template("400.html"), 400

    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(
            "Page not found: method=%s path=%s",
            request.method,
            request.path,
        )
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        app.logger.error(
            "Server error: method=%s path=%s",
            request.method,
            request.path,
            exc_info=getattr(error, "original_exception", error),
        )
        return render_template("500.html"), 500

    return app
