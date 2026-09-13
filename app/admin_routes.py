
from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import current_user

from .extensions import db
from .models import User, Course, TeacherRequest
from .decorators import role_required


def register_admin_routes(app):

    @app.route("/users")
    @role_required("admin", "superadmin")
    def users():

        users = User.query.all()

        return render_template(
            "users.html",
            users=users
        )


    @app.route("/users/<int:user_id>")
    @role_required("admin", "superadmin")
    def user_profile(user_id):

        user = db.session.get(User, user_id)

        if user is None:
            abort(404)

        return render_template(
            "user_profile.html",
            user=user
        )


    @app.route("/admin")
    @role_required("admin", "superadmin")
    def admin():

        users_count = User.query.count()

        teachers_count = User.query.filter_by(
            role="teacher"
        ).count()

        students_count = User.query.filter_by(
            role="student"
        ).count()

        courses_count = Course.query.count()

        return render_template(
            "admin.html",
            users_count=users_count,
            teachers_count=teachers_count,
            students_count=students_count,
            courses_count=courses_count,
        )


    @app.route(
        "/teacher-request",
        methods=["GET", "POST"]
    )
    @role_required("student")
    def teacher_request():

        if request.method == "POST":

            experience = request.form["experience"].strip()

            reason = request.form["reason"].strip()

            if not experience or not reason:

                flash(
                    "Experience and reason are required.",
                    "error"
                )

                return render_template(
                    "teacher_request.html"
                )

            pending_request = TeacherRequest.query.filter_by(
                user_id=current_user.id,
                status="pending",
            ).first()

            if pending_request:

                flash(
                    "You already have a pending teacher request.",
                    "error"
                )

                return redirect(
                    url_for("teacher_request")
                )

            teacher_request = TeacherRequest(
                user_id=current_user.id,
                experience=experience,
                reason=reason,
                status="pending",
            )

            db.session.add(teacher_request)

            db.session.commit()

            flash(
                "Teacher request submitted successfully.",
                "success"
            )

            return redirect(
                url_for("teacher_request")
            )

        latest_request = TeacherRequest.query.filter_by(
            user_id=current_user.id,
        ).order_by(
            TeacherRequest.created_at.desc()
        ).first()

        return render_template(
            "teacher_request.html",
            teacher_request=latest_request,
        )


    @app.route("/admin/teacher-requests")
    @role_required("admin", "superadmin")
    def teacher_requests():

        requests = TeacherRequest.query.order_by(
            TeacherRequest.created_at.desc()
        ).all()

        return render_template(
            "teacher_requests.html",
            requests=requests
        )


    @app.route(
        "/admin/teacher-requests/<int:request_id>/<action>",
        methods=["POST"]
    )
    @role_required("admin", "superadmin")
    def review_teacher_request(
        request_id,
        action
    ):

        teacher_request = db.session.get(
            TeacherRequest,
            request_id
        )

        if teacher_request is None:
            abort(404)

        if action not in ("approve", "reject"):
            abort(400)

        if teacher_request.status != "pending":

            flash(
                "This request has already been reviewed.",
                "error"
            )

            return redirect(
                url_for("teacher_requests")
            )

        if action == "approve":

            teacher_request.status = "approved"

            teacher_request.user.role = "teacher"

            flash(
                "Teacher request approved. User is now a teacher.",
                "success",
            )

        else:

            teacher_request.status = "rejected"

            flash(
                "Teacher request rejected.",
                "success"
            )

        db.session.commit()

        return redirect(
            url_for("teacher_requests")
        )


    @app.route(
        "/admin/users/<int:user_id>/role",
        methods=["POST"]
    )
    @role_required("admin", "superadmin")
    def change_user_role(user_id):

        user = db.session.get(
            User,
            user_id
        )

        if user is None:
            abort(404)

        new_role = request.form.get("role")

        if new_role not in (
            "student",
            "teacher",
            "admin",
            "superadmin",
        ):
            abort(400)

        if user.id == current_user.id:

            flash(
                "You cannot change your own role.",
                "error"
            )

            return redirect(
                url_for("users")
            )

        if current_user.role == "admin":

            if user.role in (
                "admin",
                "superadmin",
            ):
                abort(403)

            if new_role not in (
                "student",
                "teacher",
            ):
                abort(403)

        if (
            current_user.role != "superadmin"
            and user.role in ("admin", "superadmin")
        ):
            abort(403)

        user.role = new_role

        db.session.commit()

        flash(
            "User role updated successfully.",
            "success"
        )

        return redirect(
            url_for("users")
        )

