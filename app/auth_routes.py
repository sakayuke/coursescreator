import re

from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user

from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db
from .models import User


def validate_password(password):

    if len(password) < 8:
        return "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."

    if not re.search(r"\d", password):
        return "Password must contain at least one digit."

    if not re.search(
        r"""[!@#$%^&*(),.?":{}|<>_\-\\\[\]/+=;\'`~]""",
        password
    ):
        return "Password must contain at least one special character."

    return None


def register_auth_routes(app):

    @app.route(
        "/register",
        methods=["GET", "POST"]
    )
    def register():

        if request.method == "POST":

            first_name = request.form[
                "first_name"
            ].strip()

            last_name = request.form[
                "last_name"
            ].strip()

            email = request.form[
                "email"
            ].strip().lower()

            password = request.form[
                "password"
            ]

            password_confirm = request.form[
                "password_confirm"
            ]

            if not first_name or not last_name:

                return render_template(
                    "register.html"
                )

            if password != password_confirm:

                return render_template(
                    "register.html"
                )

            password_error = validate_password(
                password
            )

            if password_error:

                return render_template(
                    "register.html"
                )

            existing_user = User.query.filter_by(
                email=email
            ).first()

            if existing_user:

                return render_template(
                    "register.html"
                )

            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=generate_password_hash(password),
                role="student"
            )

            db.session.add(user)
            db.session.commit()

            return redirect(
                url_for("login")
            )

        return render_template(
            "register.html"
        )


    @app.route(
        "/login",
        methods=["GET", "POST"]
    )
    def login():

        if request.method == "POST":

            email = request.form[
                "email"
            ].strip().lower()

            password = request.form[
                "password"
            ]

            user = User.query.filter_by(
                email=email
            ).first()

            if user and check_password_hash(
                user.password_hash,
                password
            ):

                login_user(user)

                if user.role in (
                    "admin",
                    "superadmin"
                ):
                    return redirect(
                        url_for("users")
                    )

                return redirect(
                    url_for("courses")
                )

            return "Invalid email or password"

        return render_template(
            "login.html"
        )


    @app.route("/logout")
    def logout():

        logout_user()

        return redirect(
            url_for("login")
        )