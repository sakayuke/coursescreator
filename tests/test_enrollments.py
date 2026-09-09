import pytest
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import User, Course

@pytest.fixture
def app():
    original_database_uri = Config.SQLALCHEMY_DATABASE_URI
    original_engine_options = getattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", None)

    Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    Config.SQLALCHEMY_ENGINE_OPTIONS = {
        "execution_options": {
            "schema_translate_map": {
                "dbo": None,
            }
        }
    }

    app = create_app()
    Config.SQLALCHEMY_DATABASE_URI = original_database_uri
    if original_engine_options is None:
        del Config.SQLALCHEMY_ENGINE_OPTIONS
    else:
        Config.SQLALCHEMY_ENGINE_OPTIONS = original_engine_options

    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        connection = db.engine.raw_connection()
        connection.create_function(
            "getdate",
            0,
            lambda: __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_data(app):
    with app.app_context():
        admin = User(first_name="Admin", last_name="User", email="admin@test.com", password_hash="test", role="admin")
        teacher = User(first_name="Teacher", last_name="User", email="teacher@test.com", password_hash="test", role="teacher")
        student = User(first_name="Student", last_name="One", email="student1@test.com", password_hash="test", role="student")
        student2 = User(first_name="Student", last_name="Two", email="student2@test.com", password_hash="test", role="student")
        db.session.add_all([admin, teacher, student, student2])
        db.session.commit()

        course = Course(name="Test Course", description="Description", teacher_id=teacher.id)
        db.session.add(course)
        db.session.commit()

        return {
            "admin_id": admin.id,
            "teacher_id": teacher.id,
            "student_id": student.id,
            "student2_id": student2.id,
            "course_id": course.id,
        }

def login_user(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True

# 1. Admin views students page for a course
def test_admin_can_view_course_students_page(client, test_data):
    login_user(client, test_data["admin_id"])
    response = client.get(f"/courses/{test_data['course_id']}/students")
    assert response.status_code == 200

# 2. Teacher and student blocked from viewing course students page
def test_non_admin_cannot_view_course_students_page(client, test_data):
    login_user(client, test_data["teacher_id"])
    res_teacher = client.get(f"/courses/{test_data['course_id']}/students")
    assert res_teacher.status_code == 403

    login_user(client, test_data["student_id"])
    res_student = client.get(f"/courses/{test_data['course_id']}/students")
    assert res_student.status_code == 403

# 3. Admin successfully enrolls a student
def test_admin_can_enroll_student_to_course(app, client, test_data):
    login_user(client, test_data["admin_id"])
    response = client.post(
        f"/courses/{test_data['course_id']}/students/add",
        data={"student_id": test_data["student_id"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        course = db.session.get(Course, test_data["course_id"])
        student = db.session.get(User, test_data["student_id"])
        assert student in course.students

# 4. Enrolled student sees course in /courses list
def test_enrolled_student_sees_course_in_list(app, client, test_data):
    with app.app_context():
        course = db.session.get(Course, test_data["course_id"])
        student = db.session.get(User, test_data["student_id"])
        course.students.append(student)
        db.session.commit()

    login_user(client, test_data["student_id"])
    response = client.get("/courses")
    assert response.status_code == 200
    assert b"Test Course" in response.data

# 5. Unenrolled student does not see course in /courses list
def test_unenrolled_student_does_not_see_course_in_list(client, test_data):
    login_user(client, test_data["student2_id"])
    response = client.get("/courses")
    assert response.status_code == 200
    assert b"Test Course" not in response.data

# 6. Admin removes an enrolled student
def test_admin_can_remove_student_from_course(app, client, test_data):
    with app.app_context():
        course = db.session.get(Course, test_data["course_id"])
        student = db.session.get(User, test_data["student_id"])
        course.students.append(student)
        db.session.commit()

    login_user(client, test_data["admin_id"])
    response = client.post(
        f"/courses/{test_data['course_id']}/students/{test_data['student_id']}/remove",
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        course = db.session.get(Course, test_data["course_id"])
        student = db.session.get(User, test_data["student_id"])
        assert student not in course.students

# 7. Edge case: enroll non-existent student (400 Bad Request)
def test_enroll_non_existent_student_returns_400(client, test_data):
    login_user(client, test_data["admin_id"])
    response = client.post(
        f"/courses/{test_data['course_id']}/students/add",
        data={"student_id": 99999},
    )
    assert response.status_code == 400

# 8. Edge case: enroll a teacher instead of student (400 Bad Request)
def test_enroll_teacher_as_student_returns_400(client, test_data):
    login_user(client, test_data["admin_id"])
    response = client.post(
        f"/courses/{test_data['course_id']}/students/add",
        data={"student_id": test_data["teacher_id"]},
    )
    assert response.status_code == 400

# 9. Edge case: non-existent course returns 404
def test_enrollment_routes_non_existent_course_returns_404(client, test_data):
    login_user(client, test_data["admin_id"])
    res_get = client.get("/courses/99999/students")
    assert res_get.status_code == 404

    res_add = client.post("/courses/99999/students/add", data={"student_id": test_data["student_id"]})
    assert res_add.status_code == 404

    res_remove = client.post(f"/courses/99999/students/{test_data['student_id']}/remove")
    assert res_remove.status_code == 404