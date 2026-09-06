import pytest

from flask import abort, request
from flask_login import current_user

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import (
    User,
    Course,
    Topic,
    Material,
    TeacherRequest,
    Assignment,
    Submission,
)
from app.decorators import role_required, is_owner


@pytest.fixture
def app():
    original_database_uri = Config.SQLALCHEMY_DATABASE_URI
    original_engine_options = getattr(
        Config,
        "SQLALCHEMY_ENGINE_OPTIONS",
        None,
    )

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
    )

    with app.app_context():
        connection = db.engine.raw_connection()

        connection.create_function(
            "getdate",
            0,
            lambda: __import__("datetime").datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

        db.create_all()

        @app.route("/admin-only")
        @role_required("admin")
        def admin_only():
            return "OK"

        @app.route("/teacher-only")
        @role_required("teacher")
        def teacher_only():
            return "OK"

        @app.route(
            "/teacher-request",
            methods=["GET", "POST"],
        )
        @role_required("student")
        def teacher_request_test():
            if request.method == "POST":
                experience = request.form["experience"].strip()
                reason = request.form["reason"].strip()

                pending_request = TeacherRequest.query.filter_by(
                    user_id=current_user.id,
                    status="pending",
                ).first()

                if pending_request:
                    return "", 302

                teacher_request = TeacherRequest(
                    user_id=current_user.id,
                    experience=experience,
                    reason=reason,
                    status="pending",
                )

                db.session.add(teacher_request)
                db.session.commit()

                return "", 302

            return "OK"

        @app.route("/admin/teacher-requests")
        @role_required("admin", "superadmin")
        def teacher_requests_test():
            return "OK"

        @app.route(
            "/admin/teacher-requests/<int:request_id>/<action>",
            methods=["POST"],
        )
        @role_required("admin", "superadmin")
        def review_teacher_request_test(request_id, action):
            teacher_request = db.session.get(
                TeacherRequest,
                request_id,
            )

            if teacher_request is None:
                abort(404)

            if action == "approve":
                teacher_request.status = "approved"
                teacher_request.user.role = "teacher"

            elif action == "reject":
                teacher_request.status = "rejected"

            else:
                abort(400)

            db.session.commit()

            return "", 302

        @app.route(
            "/test/submissions/<int:submission_id>/grade",
            methods=["POST"],
        )
        @role_required("teacher", "admin", "superadmin")
        def test_grade_submission(submission_id):
            submission = db.session.get(
                Submission,
                submission_id,
            )

            if submission is None:
                abort(404)

            course = submission.assignment.topic.course

            if current_user.role == "teacher":
                if course.teacher_id != current_user.id:
                    abort(403)

            grade = request.form.get("grade", "").strip()
            feedback = request.form.get("feedback", "").strip()

            if not grade:
                abort(400)

            try:
                grade = int(grade)
            except ValueError:
                abort(400)

            if grade < 0 or grade > 100:
                abort(400)

            submission.grade = grade
            submission.feedback = feedback or None

            db.session.commit()

            return "", 204

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_ids(app):
    with app.app_context():
        admin = User(
            first_name="Admin",
            last_name="Test",
            email="admin@test.com",
            password_hash="test",
            role="admin",
        )

        teacher = User(
            first_name="Teacher",
            last_name="Test",
            email="teacher@test.com",
            password_hash="test",
            role="teacher",
        )

        other_teacher = User(
            first_name="Other",
            last_name="Teacher",
            email="other@test.com",
            password_hash="test",
            role="teacher",
        )

        student = User(
            first_name="Student",
            last_name="Test",
            email="student@test.com",
            password_hash="test",
            role="student",
        )

        db.session.add_all(
            [
                admin,
                teacher,
                other_teacher,
                student,
            ]
        )

        db.session.commit()

        return {
            "admin": admin.id,
            "teacher": teacher.id,
            "other_teacher": other_teacher.id,
            "student": student.id,
        }


def login_user(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def create_submission_data():
    teacher = User(
        first_name="Teacher",
        last_name="Test",
        email="submission-teacher@test.com",
        password_hash="hash",
        role="teacher",
    )

    other_teacher = User(
        first_name="Other",
        last_name="Teacher",
        email="submission-other-teacher@test.com",
        password_hash="hash",
        role="teacher",
    )

    student = User(
        first_name="Student",
        last_name="Test",
        email="submission-student@test.com",
        password_hash="hash",
        role="student",
    )

    other_student = User(
        first_name="Other",
        last_name="Student",
        email="submission-other-student@test.com",
        password_hash="hash",
        role="student",
    )

    admin = User(
        first_name="Admin",
        last_name="Test",
        email="submission-admin@test.com",
        password_hash="hash",
        role="admin",
    )

    course = Course(
        name="Test Course",
        description="Test course",
        teacher=teacher,
    )

    other_course = Course(
        name="Other Course",
        description="Other course",
        teacher=other_teacher,
    )

    topic = Topic(
        name="Test Topic",
        description="Test topic",
        course=course,
    )

    other_topic = Topic(
        name="Other Topic",
        description="Other topic",
        course=other_course,
    )

    assignment = Assignment(
        title="Test Assignment",
        description="Test assignment",
        topic=topic,
    )

    other_assignment = Assignment(
        title="Other Assignment",
        description="Other assignment",
        topic=other_topic,
    )

    submission = Submission(
        assignment=assignment,
        student=student,
        content="My submission",
    )

    other_submission = Submission(
        assignment=other_assignment,
        student=other_student,
        content="Other submission",
    )

    db.session.add_all(
        [
            teacher,
            other_teacher,
            student,
            other_student,
            admin,
            course,
            other_course,
            topic,
            other_topic,
            assignment,
            other_assignment,
            submission,
            other_submission,
        ]
    )

    db.session.commit()

    return {
        "teacher": teacher,
        "other_teacher": other_teacher,
        "student": student,
        "other_student": other_student,
        "admin": admin,
        "course": course,
        "other_course": other_course,
        "topic": topic,
        "other_topic": other_topic,
        "assignment": assignment,
        "other_assignment": other_assignment,
        "submission": submission,
        "other_submission": other_submission,
    }


def test_admin_can_access_admin_route(client, user_ids):
    login_user(client, user_ids["admin"])

    response = client.get("/admin-only")

    assert response.status_code == 200
    assert response.data == b"OK"


def test_student_cannot_access_admin_route(client, user_ids):
    login_user(client, user_ids["student"])

    response = client.get("/admin-only")

    assert response.status_code == 403


def test_teacher_can_access_teacher_route(client, user_ids):
    login_user(client, user_ids["teacher"])

    response = client.get("/teacher-only")

    assert response.status_code == 200
    assert response.data == b"OK"


def test_is_owner_returns_true_for_owner(app, user_ids):
    with app.app_context():
        teacher = db.session.get(
            User,
            user_ids["teacher"],
        )

        course = Course(
            name="Test Course",
            description="Test",
            teacher_id=teacher.id,
        )

        db.session.add(course)
        db.session.commit()

        assert is_owner(course, teacher) is True


def test_is_owner_returns_false_for_other_teacher(app, user_ids):
    with app.app_context():
        teacher = db.session.get(
            User,
            user_ids["teacher"],
        )

        other_teacher = db.session.get(
            User,
            user_ids["other_teacher"],
        )

        course = Course(
            name="Test Course",
            description="Test",
            teacher_id=teacher.id,
        )

        db.session.add(course)
        db.session.commit()

        assert is_owner(course, other_teacher) is False


def test_student_can_create_teacher_request(
    client,
    app,
    user_ids,
):
    login_user(client, user_ids["student"])

    response = client.post(
        "/teacher-request",
        data={
            "experience": "I have teaching experience.",
            "reason": "I want to teach programming.",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        teacher_request = TeacherRequest.query.filter_by(
            user_id=user_ids["student"],
        ).first()

        assert teacher_request is not None
        assert teacher_request.experience == (
            "I have teaching experience."
        )
        assert teacher_request.reason == (
            "I want to teach programming."
        )
        assert teacher_request.status == "pending"


def test_student_cannot_create_second_pending_request(
    client,
    app,
    user_ids,
):
    login_user(client, user_ids["student"])

    first_response = client.post(
        "/teacher-request",
        data={
            "experience": "First experience.",
            "reason": "First reason.",
        },
    )

    assert first_response.status_code == 302

    second_response = client.post(
        "/teacher-request",
        data={
            "experience": "Second experience.",
            "reason": "Second reason.",
        },
    )

    assert second_response.status_code == 302

    with app.app_context():
        requests = TeacherRequest.query.filter_by(
            user_id=user_ids["student"],
        ).all()

        assert len(requests) == 1


def test_admin_can_approve_teacher_request(
    client,
    app,
    user_ids,
):
    with app.app_context():
        teacher_request = TeacherRequest(
            user_id=user_ids["student"],
            experience="Teaching experience.",
            reason="I want to become a teacher.",
            status="pending",
        )

        db.session.add(teacher_request)
        db.session.commit()

        request_id = teacher_request.id

    login_user(client, user_ids["admin"])

    response = client.post(
        f"/admin/teacher-requests/{request_id}/approve"
    )

    assert response.status_code == 302

    with app.app_context():
        teacher_request = db.session.get(
            TeacherRequest,
            request_id,
        )

        student = db.session.get(
            User,
            user_ids["student"],
        )

        assert teacher_request.status == "approved"
        assert student.role == "teacher"


def test_admin_can_reject_teacher_request(
    client,
    app,
    user_ids,
):
    with app.app_context():
        teacher_request = TeacherRequest(
            user_id=user_ids["student"],
            experience="Teaching experience.",
            reason="I want to become a teacher.",
            status="pending",
        )

        db.session.add(teacher_request)
        db.session.commit()

        request_id = teacher_request.id

    login_user(client, user_ids["admin"])

    response = client.post(
        f"/admin/teacher-requests/{request_id}/reject"
    )

    assert response.status_code == 302

    with app.app_context():
        teacher_request = db.session.get(
            TeacherRequest,
            request_id,
        )

        student = db.session.get(
            User,
            user_ids["student"],
        )

        assert teacher_request.status == "rejected"
        assert student.role == "student"


def test_student_cannot_access_teacher_requests_admin_page(
    client,
    user_ids,
):
    login_user(client, user_ids["student"])

    response = client.get(
        "/admin/teacher-requests"
    )

    assert response.status_code == 403


def test_teacher_can_grade_submission(
    app,
    client,
):
    teacher = User(
        first_name="Teacher",
        last_name="One",
        email="grade-teacher@test.com",
        password_hash="hash",
        role="teacher",
    )

    student = User(
        first_name="Student",
        last_name="One",
        email="grade-student@test.com",
        password_hash="hash",
        role="student",
    )

    course = Course(
        name="Python",
        description="Python course",
        teacher=teacher,
    )

    topic = Topic(
        name="Basics",
        description="Basics",
        course=course,
    )

    assignment = Assignment(
        title="Loops",
        description="Solve loops",
        topic=topic,
    )

    submission = Submission(
        assignment=assignment,
        student=student,
        content="My solution",
    )

    with app.app_context():
        db.session.add_all(
            [
                teacher,
                student,
                course,
                topic,
                assignment,
                submission,
            ]
        )

        db.session.commit()

        submission_id = submission.id
        teacher_id = teacher.id

    login_user(client, teacher_id)

    response = client.post(
        f"/test/submissions/{submission_id}/grade",
        data={
            "grade": "87",
            "feedback": "Good work!",
        },
    )

    assert response.status_code == 204

    with app.app_context():
        submission = db.session.get(
            Submission,
            submission_id,
        )

        assert submission.grade == 87
        assert submission.feedback == "Good work!"


def test_teacher_cannot_grade_submission_from_other_course(
    app,
    client,
):
    teacher = User(
        first_name="Teacher",
        last_name="One",
        email="teacher1@test.com",
        password_hash="hash",
        role="teacher",
    )

    other_teacher = User(
        first_name="Teacher",
        last_name="Two",
        email="teacher2@test.com",
        password_hash="hash",
        role="teacher",
    )

    student = User(
        first_name="Student",
        last_name="One",
        email="student2@test.com",
        password_hash="hash",
        role="student",
    )

    course = Course(
        name="Python",
        description="Python course",
        teacher=other_teacher,
    )

    topic = Topic(
        name="Basics",
        description="Basics",
        course=course,
    )

    assignment = Assignment(
        title="Loops",
        description="Solve loops",
        topic=topic,
    )

    submission = Submission(
        assignment=assignment,
        student=student,
        content="My submission",
    )

    with app.app_context():
        db.session.add_all(
            [
                teacher,
                other_teacher,
                student,
                course,
                topic,
                assignment,
                submission,
            ]
        )

        db.session.commit()

        submission_id = submission.id
        teacher_id = teacher.id

    login_user(client, teacher_id)

    response = client.post(
        f"/test/submissions/{submission_id}/grade",
        data={
            "grade": "100",
            "feedback": "Perfect!",
        },
    )

    assert response.status_code == 403

    with app.app_context():
        submission = db.session.get(
            Submission,
            submission_id,
        )

        assert submission.grade is None
        assert submission.feedback is None


def test_student_cannot_grade_submission(
    app,
    client,
):
    teacher = User(
        first_name="Teacher",
        last_name="One",
        email="teacher3@test.com",
        password_hash="hash",
        role="teacher",
    )

    student = User(
        first_name="Student",
        last_name="One",
        email="student3@test.com",
        password_hash="hash",
        role="student",
    )

    course = Course(
        name="Python",
        description="Python course",
        teacher=teacher,
    )

    topic = Topic(
        name="Basics",
        description="Basics",
        course=course,
    )

    assignment = Assignment(
        title="Loops",
        description="Solve loops",
        topic=topic,
    )

    submission = Submission(
        assignment=assignment,
        student=student,
        content="My submission",
    )

    with app.app_context():
        db.session.add_all(
            [
                teacher,
                student,
                course,
                topic,
                assignment,
                submission,
            ]
        )

        db.session.commit()

        submission_id = submission.id
        student_id = student.id

    login_user(client, student_id)

    response = client.post(
        f"/test/submissions/{submission_id}/grade",
        data={
            "grade": "100",
            "feedback": "I am perfect!",
        },
    )

    assert response.status_code == 403

    with app.app_context():
        submission = db.session.get(
            Submission,
            submission_id,
        )

        assert submission.grade is None
        assert submission.feedback is None


def test_grade_must_be_between_0_and_100(
    app,
    client,
):
    teacher = User(
        first_name="Teacher",
        last_name="One",
        email="teacher4@test.com",
        password_hash="hash",
        role="teacher",
    )

    student = User(
        first_name="Student",
        last_name="One",
        email="student4@test.com",
        password_hash="hash",
        role="student",
    )

    course = Course(
        name="Python",
        description="Python course",
        teacher=teacher,
    )

    topic = Topic(
        name="Basics",
        description="Basics",
        course=course,
    )

    assignment = Assignment(
        title="Loops",
        description="Solve loops",
        topic=topic,
    )

    submission = Submission(
        assignment=assignment,
        student=student,
        content="My submission",
    )

    with app.app_context():
        db.session.add_all(
            [
                teacher,
                student,
                course,
                topic,
                assignment,
                submission,
            ]
        )

        db.session.commit()

        submission_id = submission.id
        teacher_id = teacher.id

    login_user(client, teacher_id)

    response = client.post(
        f"/test/submissions/{submission_id}/grade",
        data={
            "grade": "101",
            "feedback": "Invalid",
        },
    )

    assert response.status_code == 400

    with app.app_context():
        submission = db.session.get(
            Submission,
            submission_id,
        )

        assert submission.grade is None
        assert submission.feedback is None


def test_teacher_can_grade_real_submission(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        teacher_id = data["teacher"].id
        submission_id = data["submission"].id

    login_user(client, teacher_id)

    response = client.post(
        f"/submissions/{submission_id}/grade",
        data={
            "grade": "95",
            "feedback": "Excellent work!",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        updated = db.session.get(
            Submission,
            submission_id,
        )

        assert updated.grade == 95
        assert updated.feedback == "Excellent work!"


def test_teacher_cannot_grade_real_submission_from_other_course(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        teacher_id = data["teacher"].id
        submission_id = data["other_submission"].id

    login_user(client, teacher_id)

    response = client.post(
        f"/submissions/{submission_id}/grade",
        data={
            "grade": "90",
            "feedback": "Test",
        },
    )

    assert response.status_code == 403

    with app.app_context():
        updated = db.session.get(
            Submission,
            submission_id,
        )

        assert updated.grade is None
        assert updated.feedback is None


def test_student_cannot_grade_real_submission(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student_id = data["student"].id
        submission_id = data["submission"].id

    login_user(client, student_id)

    response = client.post(
        f"/submissions/{submission_id}/grade",
        data={
            "grade": "90",
            "feedback": "Test",
        },
    )

    assert response.status_code == 403

    with app.app_context():
        updated = db.session.get(
            Submission,
            submission_id,
        )

        assert updated.grade is None
        assert updated.feedback is None


def test_student_can_view_own_submission(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student_id = data["student"].id
        submission_id = data["submission"].id

    login_user(client, student_id)

    response = client.get(
        f"/submissions/{submission_id}"
    )

    assert response.status_code == 200


def test_student_cannot_view_other_student_submission(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student_id = data["student"].id
        other_submission_id = data["other_submission"].id

    login_user(client, student_id)

    response = client.get(
        f"/submissions/{other_submission_id}"
    )

    assert response.status_code == 403


def test_admin_can_grade_real_submission(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        admin_id = data["admin"].id
        submission_id = data["submission"].id

    login_user(client, admin_id)

    response = client.post(
        f"/submissions/{submission_id}/grade",
        data={
            "grade": "85",
            "feedback": "Good work.",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        updated = db.session.get(
            Submission,
            submission_id,
        )

        assert updated.grade == 85
        assert updated.feedback == "Good work."


def test_student_cannot_create_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student_id = data["student"].id
        topic_id = data["topic"].id

    login_user(client, student_id)

    response = client.get(
        f"/topics/{topic_id}/assignments/create"
    )

    assert response.status_code == 403


def test_student_cannot_edit_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student_id = data["student"].id
        assignment_id = data["assignment"].id

    login_user(client, student_id)

    response = client.get(
        f"/assignments/{assignment_id}/edit"
    )

    assert response.status_code == 403


def test_student_cannot_delete_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student_id = data["student"].id
        assignment_id = data["assignment"].id

    login_user(client, student_id)

    response = client.post(
        f"/assignments/{assignment_id}/delete"
    )

    assert response.status_code == 403


def test_student_can_submit_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student = data["student"]
        course = data["course"]
        assignment_id = data["assignment"].id

        Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student.id,
        ).delete()

        course.students.append(student)

        db.session.commit()

        student_id = student.id

    login_user(client, student_id)

    response = client.post(
        f"/assignments/{assignment_id}/submit",
        data={
            "content": "My answer"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student_id,
        ).first()

        assert submission is not None
        assert submission.content == "My answer"


def test_student_cannot_submit_assignment_twice(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student = data["student"]
        course = data["course"]
        assignment_id = data["assignment"].id

        Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student.id,
        ).delete()

        course.students.append(student)

        db.session.commit()

        student_id = student.id

    login_user(client, student_id)

    first_response = client.post(
        f"/assignments/{assignment_id}/submit",
        data={
            "content": "First answer"
        }
    )

    assert first_response.status_code == 302

    second_response = client.post(
        f"/assignments/{assignment_id}/submit",
        data={
            "content": "Second answer"
        }
    )

    assert second_response.status_code == 302

    with app.app_context():
        submissions = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student_id,
        ).all()

        assert len(submissions) == 1
        assert submissions[0].content == "First answer"


def test_student_cannot_submit_to_unenrolled_course(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        student_id = data["student"].id
        assignment_id = data["assignment"].id

    login_user(client, student_id)

    response = client.post(
        f"/assignments/{assignment_id}/submit",
        data={
            "content": "I should not be able to submit"
        }
    )

    assert response.status_code == 403


def test_teacher_can_create_assignment_in_own_course(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        teacher_id = data["teacher"].id
        topic_id = data["topic"].id

    login_user(client, teacher_id)

    response = client.post(
        f"/topics/{topic_id}/assignments/create",
        data={
            "title": "New Assignment",
            "description": "Assignment description"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        assignment = Assignment.query.filter_by(
            topic_id=topic_id,
            title="New Assignment"
        ).first()

        assert assignment is not None


def test_teacher_cannot_create_assignment_in_other_course(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        teacher_id = data["teacher"].id
        other_topic_id = data["other_topic"].id

    login_user(client, teacher_id)

    response = client.post(
        f"/topics/{other_topic_id}/assignments/create",
        data={
            "title": "Forbidden Assignment",
            "description": "Should not be created"
        }
    )

    assert response.status_code == 403


def test_teacher_can_edit_own_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        teacher_id = data["teacher"].id
        assignment_id = data["assignment"].id

    login_user(client, teacher_id)

    response = client.post(
        f"/assignments/{assignment_id}/edit",
        data={
            "title": "Updated Assignment",
            "description": "Updated description"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        assignment = db.session.get(
            Assignment,
            assignment_id,
        )

        assert assignment.title == "Updated Assignment"
        assert assignment.description == "Updated description"


def test_teacher_cannot_edit_other_teacher_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        teacher_id = data["teacher"].id
        other_assignment_id = data["other_assignment"].id

    login_user(client, teacher_id)

    response = client.post(
        f"/assignments/{other_assignment_id}/edit",
        data={
            "title": "Forbidden Update",
            "description": "Should not update"
        }
    )

    assert response.status_code == 403


def test_teacher_can_view_own_assignment_submissions(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        teacher_id = data["teacher"].id
        assignment_id = data["assignment"].id

    login_user(client, teacher_id)

    response = client.get(
        f"/assignments/{assignment_id}/submissions"
    )

    assert response.status_code == 200


def test_teacher_cannot_view_other_teacher_assignment_submissions(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        teacher_id = data["teacher"].id
        other_assignment_id = data["other_assignment"].id

    login_user(client, teacher_id)

    response = client.get(
        f"/assignments/{other_assignment_id}/submissions"
    )

    assert response.status_code == 403


def test_admin_can_create_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        admin_id = data["admin"].id
        topic_id = data["topic"].id

    login_user(client, admin_id)

    response = client.post(
        f"/topics/{topic_id}/assignments/create",
        data={
            "title": "Admin Assignment",
            "description": "Created by admin"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        assignment = Assignment.query.filter_by(
            topic_id=topic_id,
            title="Admin Assignment"
        ).first()

        assert assignment is not None


def test_admin_can_edit_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        admin_id = data["admin"].id
        assignment_id = data["assignment"].id

    login_user(client, admin_id)

    response = client.post(
        f"/assignments/{assignment_id}/edit",
        data={
            "title": "Admin Updated Assignment",
            "description": "Updated by admin"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        assignment = db.session.get(
            Assignment,
            assignment_id,
        )

        assert assignment.title == "Admin Updated Assignment"
        assert assignment.description == "Updated by admin"


def test_admin_can_delete_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        admin_id = data["admin"].id
        assignment_id = data["assignment"].id

    login_user(client, admin_id)

    response = client.post(
        f"/assignments/{assignment_id}/delete"
    )

    assert response.status_code == 302

    with app.app_context():
        assignment = db.session.get(
            Assignment,
            assignment_id,
        )

        assert assignment is None


def test_admin_can_view_assignment_submissions(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        admin_id = data["admin"].id
        assignment_id = data["assignment"].id

    login_user(client, admin_id)

    response = client.get(
        f"/assignments/{assignment_id}/submissions"
    )

    assert response.status_code == 200


def test_superadmin_can_manage_assignment(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        superadmin = User(
            first_name="Super",
            last_name="Admin",
            email="superadmin@test.com",
            password_hash="test",
            role="superadmin"
        )

        db.session.add(superadmin)
        db.session.commit()

        superadmin_id = superadmin.id
        assignment_id = data["assignment"].id

    login_user(client, superadmin_id)

    response = client.post(
        f"/assignments/{assignment_id}/edit",
        data={
            "title": "Superadmin Assignment",
            "description": "Updated by superadmin"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        assignment = db.session.get(
            Assignment,
            assignment_id,
        )

        assert assignment.title == "Superadmin Assignment"


def test_superadmin_can_view_assignment_submissions(app):
    client = app.test_client()

    with app.app_context():
        data = create_submission_data()

        superadmin = User(
            first_name="Super",
            last_name="Admin",
            email="superadmin2@test.com",
            password_hash="test",
            role="superadmin"
        )

        db.session.add(superadmin)
        db.session.commit()

        superadmin_id = superadmin.id
        assignment_id = data["assignment"].id

    login_user(client, superadmin_id)

    response = client.get(
        f"/assignments/{assignment_id}/submissions"
    )

    assert response.status_code == 200


def test_course_cascade_deletes_topic_material_assignment_and_submission(
    app,
):
    with app.app_context():
        teacher = User(
            first_name="Cascade",
            last_name="Teacher",
            email="cascade-teacher@test.com",
            password_hash="hash",
            role="teacher",
        )

        student = User(
            first_name="Cascade",
            last_name="Student",
            email="cascade-student@test.com",
            password_hash="hash",
            role="student",
        )

        course = Course(
            name="Cascade Course",
            description="Course for cascade test",
            teacher=teacher,
        )

        topic = Topic(
            name="Cascade Topic",
            description="Topic for cascade test",
            course=course,
        )

        material = Material(
            name="Cascade Material",
            file_path="/test/file.pdf",
            file_type="pdf",
            topic=topic,
        )

        assignment = Assignment(
            title="Cascade Assignment",
            description="Assignment for cascade test",
            topic=topic,
        )

        submission = Submission(
            assignment=assignment,
            student=student,
            content="Cascade submission",
        )

        db.session.add_all(
            [
                teacher,
                student,
                course,
                topic,
                material,
                assignment,
                submission,
            ]
        )

        db.session.commit()

        course_id = course.id
        topic_id = topic.id
        material_id = material.id
        assignment_id = assignment.id
        submission_id = submission.id

        db.session.delete(course)
        db.session.commit()

        assert db.session.get(Course, course_id) is None
        assert db.session.get(Topic, topic_id) is None
        assert db.session.get(Material, material_id) is None
        assert db.session.get(Assignment, assignment_id) is None
        assert db.session.get(Submission, submission_id) is None


def test_teacher_can_create_course_for_self(
    client,
    app,
    user_ids,
):
    login_user(client, user_ids["teacher"])

    response = client.post(
        "/courses/create",
        data={
            "name": "Teacher Course",
            "description": "Course created by teacher",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        course = Course.query.filter_by(
            name="Teacher Course"
        ).first()

        assert course is not None
        assert course.teacher_id == user_ids["teacher"]


def test_student_cannot_create_course(client, user_ids):
    login_user(client, user_ids["student"])

    response = client.post(
        "/courses/create",
        data={
            "name": "Student Course",
            "description": "Should not be created",
        },
    )

    assert response.status_code == 403


def test_teacher_cannot_edit_other_teacher_course(
    client,
    user_ids,
    app,
):
    with app.app_context():
        course = Course(
            name="Other Teacher Course",
            description="Test course",
            teacher_id=user_ids["other_teacher"],
        )

        db.session.add(course)
        db.session.commit()

        course_id = course.id

    login_user(client, user_ids["teacher"])

    response = client.post(
        f"/courses/{course_id}/edit",
        data={
            "name": "Hacked Course",
            "description": "Should not change",
            "teacher_id": user_ids["teacher"],
        },
    )

    assert response.status_code == 403

    with app.app_context():
        course = db.session.get(
            Course,
            course_id,
        )

        assert course.name == "Other Teacher Course"
        assert course.teacher_id == user_ids["other_teacher"]


def test_teacher_can_edit_own_course(
    client,
    user_ids,
    app,
):
    with app.app_context():
        course = Course(
            name="Own Course",
            description="Old description",
            teacher_id=user_ids["teacher"],
        )

        db.session.add(course)
        db.session.commit()

        course_id = course.id

    login_user(client, user_ids["teacher"])

    response = client.post(
        f"/courses/{course_id}/edit",
        data={
            "name": "Updated Course",
            "description": "Updated description",
        },
    )

    assert response.status_code == 302

    with app.app_context():
        course = db.session.get(
            Course,
            course_id,
        )

        assert course.name == "Updated Course"
        assert course.description == "Updated description"


def test_teacher_cannot_delete_other_teacher_course(
    client,
    user_ids,
    app,
):
    with app.app_context():
        course = Course(
            name="Protected Course",
            description="Should remain",
            teacher_id=user_ids["other_teacher"],
        )

        db.session.add(course)
        db.session.commit()

        course_id = course.id

    login_user(client, user_ids["teacher"])

    response = client.post(
        f"/courses/{course_id}/delete"
    )

    assert response.status_code == 403

    with app.app_context():
        assert db.session.get(
            Course,
            course_id,
        ) is not None


def test_teacher_can_delete_own_course(
    client,
    user_ids,
    app,
):
    with app.app_context():
        course = Course(
            name="Delete Course",
            description="Will be deleted",
            teacher_id=user_ids["teacher"],
        )

        db.session.add(course)
        db.session.commit()

        course_id = course.id

    login_user(client, user_ids["teacher"])

    response = client.post(
        f"/courses/{course_id}/delete"
    )

    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(
            Course,
            course_id,
        ) is None


def test_student_cannot_delete_course(
    client,
    user_ids,
    app,
):
    with app.app_context():
        course = Course(
            name="Student Delete Test",
            description="Should remain",
            teacher_id=user_ids["teacher"],
        )

        db.session.add(course)
        db.session.commit()

        course_id = course.id

    login_user(client, user_ids["student"])

    response = client.post(
        f"/courses/{course_id}/delete"
    )

    assert response.status_code == 403

    with app.app_context():
        assert db.session.get(
            Course,
            course_id,
        ) is not None