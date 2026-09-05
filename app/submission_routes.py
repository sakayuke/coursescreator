from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import current_user, login_required

from .extensions import db
from .models import Submission
from .decorators import role_required


def register_submission_routes(app):

    @app.route("/submissions/<int:submission_id>")
    @login_required
    def view_submission(submission_id):
        submission = db.session.get(Submission, submission_id)

        if submission is None:
            abort(404)

        course = submission.assignment.topic.course

        if current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        elif current_user.role == "student":
            if submission.student_id != current_user.id:
                abort(403)

        elif current_user.role not in ("admin", "superadmin"):
            abort(403)

        return render_template(
            "submission.html",
            submission=submission,
        )


    @app.route(
        "/submissions/<int:submission_id>/grade",
        methods=["POST"]
    )
    @role_required("teacher", "admin", "superadmin")
    def grade_submission(submission_id):
        submission = db.session.get(Submission, submission_id)

        if submission is None:
            abort(404)

        course = submission.assignment.topic.course

        if current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        grade = request.form.get("grade", "").strip()
        feedback = request.form.get("feedback", "").strip()

        if not grade:
            flash("Grade is required.", "error")
            return redirect(
                url_for(
                    "view_submission",
                    submission_id=submission.id
                )
            )

        try:
            grade = int(grade)
        except ValueError:
            flash("Grade must be a number.", "error")
            return redirect(
                url_for(
                    "view_submission",
                    submission_id=submission.id
                )
            )

        if grade < 0 or grade > 100:
            flash("Grade must be between 0 and 100.", "error")
            return redirect(
                url_for(
                    "view_submission",
                    submission_id=submission.id
                )
            )

        submission.grade = grade
        submission.feedback = feedback or None

        db.session.commit()

        flash(
            "Grade and feedback updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "view_submission",
                submission_id=submission.id
            )
        )