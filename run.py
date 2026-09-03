from app.decorators import role_required
from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app import create_app
from app.extensions import db
from app.models import User, Course, Topic, Material

app = create_app()


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/users")
@login_required
@role_required("admin")
def users():
    users = User.query.all()

    return render_template(
        "users.html",
        users=users
    )

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
        username = request.form["username"]
        password = request.form["password"]
        password_confirm = request.form["password_confirm"]

        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash("This username is already taken.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        user = User(
            username=username,
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
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            if user.role == "admin":
                return redirect(url_for("users"))
            else:
                return redirect(url_for("courses"))

        return "Invalid username or password"

    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/admin")
@role_required("admin")
def admin():
    return "Welcome, Admin!"

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
        if course.teacher_id != current_user.id:
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
        if course.teacher_id != current_user.id:
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