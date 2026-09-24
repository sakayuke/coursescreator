
from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import current_user
from .extensions import db
from .models import Assignment, Topic, Submission
from .decorators import role_required


def register_assignment_routes(app):

    @app.route("/topics/<int:topic_id>/assignments")
    @role_required("teacher", "admin", "superadmin", "student")
    def assignments(topic_id):

        topic = db.session.get(Topic, topic_id)

        if topic is None:
            abort(404)

        course = topic.course

        if current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        elif current_user.role == "student":
            if current_user not in course.students:
                abort(403)

        query = request.args.get("q", "").strip()

        assignments_query = Assignment.query.filter_by(
            topic_id=topic.id
        )

        if query:
            assignments_query = assignments_query.filter(
                Assignment.title.ilike(f"%{query}%")
            )

        assignments = assignments_query.all()

        status = request.args.get("status", "all")
        if current_user.role == "student":
            valid_statuses = {
                "all",
                "not_submitted",
                "submitted",
            }

            if status not in valid_statuses:
                status = "all"

            if status != "all":
                def matches_status(assignment):
                    submission = next(
                        (
                            item for item in assignment.submissions
                            if item.student_id == current_user.id
                        ),
                        None
                    )

                    if status == "not_submitted":
                        return submission is None

                    return submission is not None

                assignments = [
                    assignment for assignment in assignments
                    if matches_status(assignment)
                ]

        else:
            status = "all"

        return render_template(
            "assignments.html",
            topic=topic,
            course=course,
            assignments=assignments,
            query=query,
            status=status
        )


    @app.route("/assignments/<int:assignment_id>")
    @role_required("teacher", "admin", "superadmin", "student")
    def view_assignment(assignment_id):

        assignment = db.session.get(Assignment, assignment_id)

        if assignment is None:
            abort(404)

        topic = assignment.topic
        course = topic.course

        if current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        elif current_user.role == "student":
            if current_user not in course.students:
                abort(403)

        submission = None

        if current_user.role == "student":
            submission = Submission.query.filter_by(
                assignment_id=assignment.id,
                student_id=current_user.id
            ).first()

        return render_template(
            "assignment.html",
            assignment=assignment,
            topic=topic,
            course=course,
            submission=submission
        )


    @app.route(
        "/topics/<int:topic_id>/assignments/create",
        methods=["GET", "POST"]
    )
    @role_required("teacher", "admin", "superadmin")
    def create_assignment(topic_id):

        topic = db.session.get(Topic, topic_id)

        if topic is None:
            abort(404)

        course = topic.course

        if current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        if request.method == "POST":

            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()

            if not title:
                flash("Title is required.", "error")

                return render_template(
                    "create_assignment.html",
                    topic=topic,
                    course=course
                )

            if not description:
                flash("Description is required.", "error")

                return render_template(
                    "create_assignment.html",
                    topic=topic,
                    course=course
                )

            assignment = Assignment(
                topic_id=topic.id,
                title=title,
                description=description
            )

            db.session.add(assignment)
            db.session.commit()

            flash(
                "Assignment created successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "assignments",
                    topic_id=topic.id
                )
            )

        return render_template(
            "create_assignment.html",
            topic=topic,
            course=course
        )


    @app.route(
        "/assignments/<int:assignment_id>/edit",
        methods=["GET", "POST"]
    )
    @role_required("teacher", "admin", "superadmin")
    def edit_assignment(assignment_id):

        assignment = db.session.get(
            Assignment,
            assignment_id
        )

        if assignment is None:
            abort(404)

        topic = assignment.topic
        course = topic.course

        if current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        if request.method == "POST":

            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()

            if not title:
                flash("Title is required.", "error")

                return render_template(
                    "edit_assignment.html",
                    assignment=assignment,
                    topic=topic,
                    course=course
                )

            if not description:
                flash("Description is required.", "error")

                return render_template(
                    "edit_assignment.html",
                    assignment=assignment,
                    topic=topic,
                    course=course
                )

            assignment.title = title
            assignment.description = description

            db.session.commit()

            flash(
                "Assignment updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "assignments",
                    topic_id=topic.id
                )
            )

        return render_template(
            "edit_assignment.html",
            assignment=assignment,
            topic=topic,
            course=course
        )


    @app.route(
        "/assignments/<int:assignment_id>/delete",
        methods=["POST"]
    )
    @role_required("teacher", "admin", "superadmin")
    def delete_assignment(assignment_id):

        assignment = db.session.get(
            Assignment,
            assignment_id
        )

        if assignment is None:
            abort(404)

        topic = assignment.topic
        course = topic.course

        if current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        db.session.delete(assignment)
        db.session.commit()

        flash(
            "Assignment deleted successfully.",
            "success"
        )

        return redirect(
            url_for(
                "assignments",
                topic_id=topic.id
            )
        )



    @app.route(
        "/assignments/<int:assignment_id>/submissions"
    )
    @role_required("teacher", "admin", "superadmin")
    def assignment_submissions(assignment_id):

        assignment = db.session.get(
            Assignment,
            assignment_id
        )

        if assignment is None:
            abort(404)

        topic = assignment.topic
        course = topic.course

        if current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        submissions = Submission.query.filter_by(
            assignment_id=assignment.id
        ).all()

        return render_template(
            "assignment_submissions.html",
            assignment=assignment,
            topic=topic,
            course=course,
            submissions=submissions
        )



    @app.route(
        "/assignments/<int:assignment_id>/submit",
        methods=["POST"]
    )
    @role_required("student")
    def submit_assignment(assignment_id):

        assignment = db.session.get(
            Assignment,
            assignment_id
        )

        if assignment is None:
            abort(404)

        topic = assignment.topic
        course = topic.course

        if current_user not in course.students:
            abort(403)

        existing_submission = Submission.query.filter_by(
            assignment_id=assignment.id,
            student_id=current_user.id
        ).first()

        if existing_submission is not None:
            flash(
                "You have already submitted this assignment.",
                "error"
            )

            return redirect(
                url_for(
                    "view_assignment",
                    assignment_id=assignment.id
                )
            )

        content = request.form.get(
            "content",
            ""
        ).strip()

        if not content:
            flash(
                "Answer is required.",
                "error"
            )

            return redirect(
                url_for(
                    "view_assignment",
                    assignment_id=assignment.id
                )
            )

        submission = Submission(
            assignment_id=assignment.id,
            student_id=current_user.id,
            content=content
        )

        db.session.add(submission)
        db.session.commit()

        flash(
            "Assignment submitted successfully.",
            "success"
        )

        return redirect(
            url_for(
                "view_assignment",
                assignment_id=assignment.id
            )
        )
