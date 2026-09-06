
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required

from .extensions import db
from .models import User


def register_profile_routes(app):

    @app.route("/profile")
    @login_required
    def profile():
        return render_template("profile.html")

    @app.route("/profile/edit", methods=["GET", "POST"])
    @login_required
    def edit_profile():

        if request.method == "POST":

            first_name = request.form["first_name"].strip()
            last_name = request.form["last_name"].strip()
            email = request.form["email"].strip().lower()

            if not first_name or not last_name or not email:
                flash(
                    "All fields are required.",
                    "error"
                )

                return render_template(
                    "edit_profile.html"
                )

            existing_user = User.query.filter(
                User.email == email,
                User.id != current_user.id
            ).first()

            if existing_user:
                flash(
                    "This email is already registered.",
                    "error"
                )

                return render_template(
                    "edit_profile.html"
                )

            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.email = email

            db.session.commit()

            flash(
                "Profile updated successfully.",
                "success"
            )

            return redirect(
                url_for("profile")
            )

        return render_template(
            "edit_profile.html"
        )

