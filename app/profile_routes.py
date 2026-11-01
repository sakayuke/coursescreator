from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import User
from .auth_routes import validate_password


def register_profile_routes(app):

    @app.route("/profile")
    @login_required
    def profile():
        return render_template("profile.html")

    @app.route("/profile/edit", methods=["GET", "POST"])
    @login_required
    def edit_profile():

        if request.method == "POST":

            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            current_password = request.form.get("current_password", "").strip()
            new_password = request.form.get("new_password", "").strip()
            new_password_confirm = request.form.get("new_password_confirm", "").strip()

            if not first_name or not last_name or not email:
                flash(
                    "All profile fields are required.",
                    "error"
                )
                return render_template("edit_profile.html")

            # Defensive verification: Email change requires current password
            if email != current_user.email:
                if not current_password:
                    flash(
                        "Current password is required to change your email address.",
                        "error"
                    )
                    return render_template("edit_profile.html")

                if not check_password_hash(current_user.password_hash, current_password):
                    flash(
                        "Current password is incorrect.",
                        "error"
                    )
                    return render_template("edit_profile.html")

                existing_user = User.query.filter(
                    User.email == email,
                    User.id != current_user.id
                ).first()

                if existing_user:
                    flash(
                        "This email is already registered.",
                        "error"
                    )
                    return render_template("edit_profile.html")

                current_user.email = email

            # Defensive verification: Optional Password change
            if new_password:
                if not current_password:
                    flash(
                        "Current password is required to set a new password.",
                        "error"
                    )
                    return render_template("edit_profile.html")

                if not check_password_hash(current_user.password_hash, current_password):
                    flash(
                        "Current password is incorrect.",
                        "error"
                    )
                    return render_template("edit_profile.html")

                if new_password != new_password_confirm:
                    flash(
                        "New passwords do not match.",
                        "error"
                    )
                    return render_template("edit_profile.html")

                password_error = validate_password(new_password)
                if password_error:
                    flash(
                        password_error,
                        "error"
                    )
                    return render_template("edit_profile.html")

                current_user.password_hash = generate_password_hash(new_password)

            current_user.first_name = first_name
            current_user.last_name = last_name

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
