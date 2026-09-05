from app.decorators import role_required, is_owner

from flask import render_template, request, redirect, url_for, abort, flash

from flask_login import login_user, logout_user, current_user, login_required

from werkzeug.security import generate_password_hash, check_password_hash

from app import create_app

from app.extensions import db

from app.models import User, Course, Topic, Material, TeacherRequest

import re

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."

    if not re.search(r"\d", password):
        return "Password must contain at least one digit."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\\[\]/+=;'`~]", password):
        return "Password must contain at least one special character."

    return None

app = create_app()

@app.cli.command("create-admin")
def create_admin():
    """Create an admin user."""

    email = input("Admin email: ").strip()
    password = input("Admin password: ")

    if not email or not password:
        print("Email and password are required.")
        return

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        print("User with this email already exists.")
        return

    password_hash = generate_password_hash(password)

    user = User(
    first_name="Admin",
    last_name="User",
    email=email,
    password_hash=password_hash,
    role="superadmin"
)


    db.session.add(user)
    db.session.commit()

    print(f"Admin {email} created successfully.")


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/users")
@role_required("admin", "superadmin")
def users():
    users = User.query.all()
    return render_template("users.html", users=users)

@app.route("/users/<int:user_id>")
@login_required
@role_required("admin")
def user_profile(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        abort(404)

    return render_template(
        "user_profile.html",
        user=user
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        password_confirm = request.form["password_confirm"]

        if not first_name or not last_name:
            flash("First name and last name are required.", "error")
            return render_template("register.html")

        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        password_error = validate_password(password)

        if password_error:
            flash(password_error, "error")
            return render_template("register.html")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("This email is already registered.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash,
            role="student"
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            if user.role == "admin":
                return redirect(url_for("users"))
            else:
                return redirect(url_for("courses"))

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


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
            flash("All fields are required.", "error")
            return render_template("edit_profile.html")

        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_user:
            flash("This email is already registered.", "error")
            return render_template("edit_profile.html")

        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email

        db.session.commit()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html")


@app.route("/admin")
@role_required("admin", "superadmin")
def admin():
    users_count = User.query.count()
    teachers_count = User.query.filter_by(role="teacher").count()
    students_count = User.query.filter_by(role="student").count()
    courses_count = Course.query.count()

    return render_template(
        "admin.html",
        users_count=users_count,
        teachers_count=teachers_count,
        students_count=students_count,
        courses_count=courses_count,
    )

@app.route("/teacher-request", methods=["GET", "POST"])
@role_required("student")
def teacher_request():
    if request.method == "POST":
        experience = request.form["experience"].strip()
        reason = request.form["reason"].strip()

        if not experience or not reason:
            flash("Experience and reason are required.", "error")
            return render_template("teacher_request.html")

        pending_request = TeacherRequest.query.filter_by(
            user_id=current_user.id,
            status="pending"
        ).first()

        if pending_request:
            flash("You already have a pending teacher request.", "error")
            return redirect(url_for("teacher_request"))

        teacher_request = TeacherRequest(
            user_id=current_user.id,
            experience=experience,
            reason=reason,
            status="pending"
        )

        db.session.add(teacher_request)
        db.session.commit()

        flash("Teacher request submitted successfully.", "success")
        return redirect(url_for("teacher_request"))

    teacher_request = TeacherRequest.query.filter_by(
        user_id=current_user.id
    ).order_by(
        TeacherRequest.created_at.desc()
    ).first()

    return render_template(
        "teacher_request.html",
        teacher_request=teacher_request
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
def review_teacher_request(request_id, action):
    teacher_request = db.session.get(TeacherRequest, request_id)

    if teacher_request is None:
        abort(404)

    if action not in ("approve", "reject"):
        abort(400)

    if teacher_request.status != "pending":
        flash("This request has already been reviewed.", "error")
        return redirect(url_for("teacher_requests"))

    if action == "approve":
        teacher_request.status = "approved"
        teacher_request.user.role = "teacher"

        flash(
            "Teacher request approved. User is now a teacher.",
            "success"
        )

    else:
        teacher_request.status = "rejected"

        flash(
            "Teacher request rejected.",
            "success"
        )

    db.session.commit()

    return redirect(url_for("teacher_requests"))

@app.route("/courses")
@login_required
def courses():
    if current_user.role == "admin":

        courses = Course.query.all()

    elif current_user.role == "teacher":

        courses = Course.query.filter_by(
            teacher_id=current_user.id
        ).all()

    else:

        courses = current_user.enrolled_courses

    return render_template(
        "courses.html",
        courses=courses
    )

@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@role_required("admin", "superadmin")
def change_user_role(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        abort(404)

    new_role = request.form["role"]

    if new_role not in ("student", "teacher", "admin", "superadmin"):
        abort(400)


    if user.id == current_user.id:
        flash("You cannot change your own role.", "error")
        return redirect(url_for("users"))


    if current_user.role == "admin":
        if user.role in ("admin", "superadmin"):
            abort(403)

        if new_role not in ("student", "teacher"):
            abort(403)


    if current_user.role == "admin" and new_role == "superadmin":
        abort(403)


    if current_user.role != "superadmin":
        if user.role in ("admin", "superadmin"):
            abort(403)

    user.role = new_role
    db.session.commit()

    flash("User role updated successfully.", "success")
    return redirect(url_for("users"))

@app.route("/courses/create", methods=["GET", "POST"])
@login_required
def create_course():
    if current_user.role not in ("admin", "teacher"):
        abort(403)

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]

        if current_user.role == "teacher":
            teacher_id = current_user.id
        else:
            teacher_id = request.form["teacher_id"]

        course = Course(
            name=name,
            description=description,
            teacher_id=teacher_id
        )

        db.session.add(course)
        db.session.commit()

        return redirect(url_for("courses"))

    teachers = User.query.filter_by(role="teacher").all()

    return render_template(
        "create_course.html",
        teachers=teachers
    )

@app.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def edit_course(course_id):
    course = db.session.get(Course, course_id)

    if course is None:
        abort(404)

    if current_user.role == "admin":
        pass
    elif current_user.role == "teacher":
        if not is_owner(course):
         abort(403)
    else:
        abort(403)

    if request.method == "POST":
        course.name = request.form["name"]
        course.description = request.form["description"]

        if current_user.role == "admin":
            course.teacher_id = request.form["teacher_id"]

        db.session.commit()

        return redirect(url_for("courses"))

    teachers = User.query.filter_by(role="teacher").all()

    return render_template(
        "edit_course.html",
        course=course,
        teachers=teachers
    )

@app.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def delete_course(course_id):
    course = db.session.get(Course, course_id)

    if course is None:
        abort(404)

    if current_user.role == "admin":
        pass
    elif current_user.role == "teacher":
        if not is_owner(course):
         abort(403)
    else:
        abort(403)

    db.session.delete(course)
    db.session.commit()

    return redirect(url_for("courses"))

@app.route("/courses/<int:course_id>/topics")
@login_required
def course_topics(course_id):
    course = db.session.get(Course, course_id)

    if course is None:
        abort(404)

    if current_user.role == "admin":
        pass

    elif current_user.role == "teacher":
        if course.teacher_id != current_user.id:
            abort(403)

    elif current_user.role == "student":
        if current_user not in course.students:
            abort(403)

    else:
        abort(403)

    topics = Topic.query.filter_by(
        course_id=course_id
    ).all()

    return render_template(
        "topics.html",
        course=course,
        topics=topics
    )

@app.route("/courses/<int:course_id>/topics/create", methods=["GET", "POST"])
@login_required
def create_topic(course_id):
    course = db.session.get(Course, course_id)

    if course is None:
        abort(404)


    if current_user.role == "admin":
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
            url_for("course_topics", course_id=course.id)
        )

    return render_template(
        "create_topic.html",
        course=course
    )

@app.route(
    "/courses/<int:course_id>/topics/<int:topic_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_topic(course_id, topic_id):
    topic = db.session.get(Topic, topic_id)

    if topic is None:
        abort(404)

    if topic.course_id != course_id:
        abort(404)

    course = db.session.get(Course, course_id)

    if current_user.role == "admin":
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
@login_required
def delete_topic(course_id, topic_id):
    topic = db.session.get(Topic, topic_id)

    if topic is None:
        abort(404)

    if topic.course_id != course_id:
        abort(404)

    course = db.session.get(Course, course_id)

    if current_user.role == "admin":
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
@login_required
def topic_materials(course_id, topic_id):

    topic = db.session.get(Topic, topic_id)

    if topic is None:
        abort(404)

    if topic.course_id != course_id:
        abort(404)

    course = db.session.get(Course, course_id)

    if current_user.role == "admin":
        pass

    elif current_user.role == "teacher":
        if course.teacher_id != current_user.id:
            abort(403)

    elif current_user.role == "student":
        if current_user not in course.students:
            abort(403)

    else:
        abort(403)

    return render_template(
        "materials.html",
        course=course,
        topic=topic
    )

@app.route("/courses/<int:course_id>/students")
@login_required
@role_required("admin")
def course_students(course_id):
    course = db.session.get(Course, course_id)

    if course is None:
        abort(404)

    students = User.query.filter_by(role="student").all()

    return render_template(
        "course_students.html",
        course=course,
        students=students
    )

@app.route(
    "/courses/<int:course_id>/students/add",
    methods=["POST"]
)
@login_required
@role_required("admin")
def add_student_to_course(course_id):
    course = db.session.get(Course, course_id)

    if course is None:
        abort(404)

    student_id = request.form["student_id"]

    student = db.session.get(User, student_id)

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
@login_required
@role_required("admin")
def remove_student_from_course(course_id, student_id):
    course = db.session.get(Course, course_id)

    if course is None:
        abort(404)

    student = db.session.get(User, student_id)

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



if __name__ == "__main__":
    app.run(debug=True)
