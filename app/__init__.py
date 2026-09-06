
from flask import Flask, render_template

from flask_migrate import Migrate

from .extensions import db, login_manager
from .config import Config


def create_app():

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.config.from_object(Config)

    db.init_app(app)

    Migrate(
        app,
        db,
        compare_type=True,
        include_schemas=True
    )

    login_manager.init_app(app)

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
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    return app

