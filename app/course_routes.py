from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import current_user, login_required

from .extensions import db
from .models import User, Course, Topic, Material, Submission
from .decorators import role_required, is_owner


def register_course_routes(app):

    @app.route("/courses")
    @login_required
    def courses():
        unread_course_ids = set()

        if current_user.role in ("admin", "superadmin"):
            courses = Course.query.all()
        elif current_user.role == "teacher":
            courses = Course.query.filter_by(
                teacher_id=current_user.id
            ).all()
        elif current_user.role == "student":
            courses = current_user.enrolled_courses
        else:
            abort(403)

        if current_user.role == "student":
            unread_submissions = Submission.query.filter(
                Submission.student_id == current_user.id,
                Submission.grade.isnot(None),
                Submission.grade_seen_at.is_(None)
            ).all()
            unread_course_ids = {
                submission.assignment.topic.course_id
                for submission in unread_submissions
            }

        query = request.args.get("q", "").strip()

        if query:
            courses = [
                course for course in courses
                if query.casefold() in course.name.casefold()
            ]

        return render_template(
            "courses.html",
            courses=courses,
            query=query,
            unread_course_ids=unread_course_ids
        )


    @app.route("/courses/create", methods=["GET", "POST"])
    def create_course():
        if current_user.role not in (
            "admin",
            "superadmin",
            "teacher"
        ):
            abort(403)

        if request.method == "POST":
            name = request.form["name"].strip()
            description = request.form["description"].strip()

            if not name:
                flash(
                    "Course name is required.",
                    "error"
                )

                return render_template(
                    "create_course.html",
                    teachers=User.query.filter_by(
                        role="teacher"
                    ).all()
                )

            if current_user.role == "teacher":
                teacher_id = current_user.id
            else:
                teacher_id = request.form["teacher_id"]

            teacher = db.session.get(
                User,
                teacher_id
            )

            if teacher is None or teacher.role != "teacher":
                flash(
                    "Selected teacher is invalid.",
                    "error"
                )

                return render_template(
                    "create_course.html",
                    teachers=User.query.filter_by(
                        role="teacher"
                    ).all()
                )

            course = Course(
                name=name,
                description=description,
                teacher_id=teacher.id
            )

            db.session.add(course)
            db.session.commit()

            flash(
                "Course created successfully.",
                "success"
            )

            return redirect(
                url_for("courses")
            )

        teachers = User.query.filter_by(
            role="teacher"
        ).all()

        return render_template(
            "create_course.html",
            teachers=teachers
        )


    @app.route(
        "/courses/<int:course_id>/edit",
        methods=["GET", "POST"]
    )
    def edit_course(course_id):
        course = db.session.get(
            Course,
            course_id
        )

        if course is None:
            abort(404)

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if not is_owner(course):
                abort(403)

        else:
            abort(403)

        if request.method == "POST":
            course.name = request.form["name"]
            course.description = request.form["description"]

            if current_user.role in (
                "admin",
                "superadmin"
            ):
                teacher_id = request.form["teacher_id"]

                teacher = db.session.get(
                    User,
                    teacher_id
                )

                if teacher is None or teacher.role != "teacher":
                    abort(400)

                course.teacher_id = teacher.id

            db.session.commit()

            return redirect(
                url_for("courses")
            )

        teachers = User.query.filter_by(
            role="teacher"
        ).all()

        return render_template(
            "edit_course.html",
            course=course,
            teachers=teachers
        )


    @app.route(
        "/courses/<int:course_id>/delete",
        methods=["POST"]
    )
    def delete_course(course_id):
        course = db.session.get(
            Course,
            course_id
        )

        if course is None:
            abort(404)

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if not is_owner(course):
                abort(403)

        else:
            abort(403)

        db.session.delete(course)
        db.session.commit()

        return redirect(
            url_for("courses")
        )


    @app.route(
        "/courses/<int:course_id>/topics"
    )
    def course_topics(course_id):
        course = db.session.get(
            Course,
            course_id
        )

        if course is None:
            abort(404)

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        elif current_user.role == "student":
            if current_user not in course.students:
                abort(403)

        else:
            abort(403)

        query = request.args.get("q", "").strip()

        topics_query = Topic.query.filter_by(
            course_id=course_id
        )

        if query:
            topics_query = topics_query.filter(
                Topic.name.ilike(f"%{query}%")
            )

        topics = topics_query.all()

        return render_template(
            "topics.html",
            course=course,
            topics=topics,
            query=query
        )


    @app.route(
        "/courses/<int:course_id>/topics/create",
        methods=["GET", "POST"]
    )
    def create_topic(course_id):
        course = db.session.get(
            Course,
            course_id
        )

        if course is None:
            abort(404)

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        else:
            abort(403)

        if request.method == "POST":
            name = request.form["name"]
            description = request.form["description"]

            topic = Topic(
                course_id=course.id,
                name=name,
                description=description
            )

            db.session.add(topic)
            db.session.commit()

            return redirect(
                url_for(
                    "course_topics",
                    course_id=course.id
                )
            )

        return render_template(
            "create_topic.html",
            course=course
        )


    @app.route(
        "/courses/<int:course_id>/topics/<int:topic_id>/edit",
        methods=["GET", "POST"]
    )
    def edit_topic(course_id, topic_id):
        topic = db.session.get(
            Topic,
            topic_id
        )

        if topic is None:
            abort(404)

        if topic.course_id != course_id:
            abort(404)

        course = db.session.get(
            Course,
            course_id
        )

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        else:
            abort(403)

        if request.method == "POST":
            topic.name = request.form["name"]
            topic.description = request.form["description"]

            db.session.commit()

            return redirect(
                url_for(
                    "course_topics",
                    course_id=course.id
                )
            )

        return render_template(
            "edit_topic.html",
            course=course,
            topic=topic
        )


    @app.route(
        "/courses/<int:course_id>/topics/<int:topic_id>/delete",
        methods=["POST"]
    )
    def delete_topic(course_id, topic_id):
        topic = db.session.get(
            Topic,
            topic_id
        )

        if topic is None:
            abort(404)

        if topic.course_id != course_id:
            abort(404)

        course = db.session.get(
            Course,
            course_id
        )

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        else:
            abort(403)

        db.session.delete(topic)
        db.session.commit()

        return redirect(
            url_for(
                "course_topics",
                course_id=course.id
            )
        )


    @app.route(
        "/courses/<int:course_id>/topics/<int:topic_id>/materials"
    )
    def topic_materials(course_id, topic_id):
        topic = db.session.get(
            Topic,
            topic_id
        )

        if topic is None:
            abort(404)

        if topic.course_id != course_id:
            abort(404)

        course = db.session.get(
            Course,
            course_id
        )

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        elif current_user.role == "student":
            if current_user not in course.students:
                abort(403)

        else:
            abort(403)

        query = request.args.get("q", "").strip()

        materials_query = Material.query.filter_by(
            topic_id=topic.id
        )

        if query:
            materials_query = materials_query.filter(
                Material.name.ilike(f"%{query}%")
            )

        materials = materials_query.all()

        return render_template(
            "materials.html",
            course=course,
            topic=topic,
            materials=materials,
            query=query
        )


    @app.route(
        "/courses/<int:course_id>/topics/<int:topic_id>/materials/create",
        methods=["GET", "POST"]
    )
    def create_material(course_id, topic_id):
        topic = db.session.get(
            Topic,
            topic_id
        )

        if topic is None:
            abort(404)

        if topic.course_id != course_id:
            abort(404)

        course = db.session.get(
            Course,
            course_id
        )

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        else:
            abort(403)

        if request.method == "POST":
            name = request.form["name"].strip()
            file_path = request.form["file_path"].strip()
            file_type = request.form.get(
                "file_type",
                ""
            ).strip()

            if not name or not file_path:
                flash(
                    "Name and file path are required.",
                    "error"
                )

                return render_template(
                    "create_material.html",
                    course=course,
                    topic=topic
                )

            material = Material(
                topic_id=topic.id,
                name=name,
                file_path=file_path,
                file_type=file_type or None
            )

            db.session.add(material)
            db.session.commit()

            flash(
                "Material added successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "topic_materials",
                    course_id=course.id,
                    topic_id=topic.id
                )
            )

        return render_template(
            "create_material.html",
            course=course,
            topic=topic
        )


    @app.route(
        "/courses/<int:course_id>/topics/<int:topic_id>/materials/<int:material_id>/delete",
        methods=["POST"]
    )
    def delete_material(
        course_id,
        topic_id,
        material_id
    ):
        material = db.session.get(
            Material,
            material_id
        )

        if material is None:
            abort(404)

        if material.topic_id != topic_id:
            abort(404)

        topic = db.session.get(
            Topic,
            topic_id
        )

        if topic is None:
            abort(404)

        if topic.course_id != course_id:
            abort(404)

        course = db.session.get(
            Course,
            course_id
        )

        if current_user.role in (
            "admin",
            "superadmin"
        ):
            pass

        elif current_user.role == "teacher":
            if course.teacher_id != current_user.id:
                abort(403)

        else:
            abort(403)

        db.session.delete(material)
        db.session.commit()

        flash(
            "Material deleted successfully.",
            "success"
        )

        return redirect(
            url_for(
                "topic_materials",
                course_id=course.id,
                topic_id=topic.id
            )
        )


    @app.route(
        "/courses/<int:course_id>/students"
    )
    @role_required(
        "admin",
        "superadmin"
    )
    def course_students(course_id):
        course = db.session.get(
            Course,
            course_id
        )

        if course is None:
            abort(404)

        students = User.query.filter_by(
            role="student"
        ).all()

        return render_template(
            "course_students.html",
            course=course,
            students=students
        )


    @app.route(
        "/courses/<int:course_id>/students/add",
        methods=["POST"]
    )
    @role_required(
        "admin",
        "superadmin"
    )
    def add_student_to_course(course_id):
        course = db.session.get(
            Course,
            course_id
        )

        if course is None:
            abort(404)

        student_id = request.form["student_id"]

        student = db.session.get(
            User,
            student_id
        )

        if student is None or student.role != "student":
            abort(400)

        if student not in course.students:
            course.students.append(student)
            db.session.commit()

        return redirect(
            url_for(
                "course_students",
                course_id=course.id
            )
        )


    @app.route(
        "/courses/<int:course_id>/students/<int:student_id>/remove",
        methods=["POST"]
    )
    @role_required(
        "admin",
        "superadmin"
    )
    def remove_student_from_course(
        course_id,
        student_id
    ):
        course = db.session.get(
            Course,
            course_id
        )

        if course is None:
            abort(404)

        student = db.session.get(
            User,
            student_id
        )

        if student is None or student.role != "student":
            abort(400)

        if student in course.students:
            course.students.remove(student)
            db.session.commit()

        return redirect(
            url_for(
                "course_students",
                course_id=course.id
            )
        )
