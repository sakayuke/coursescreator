import pytest

from flask import abort, request
from flask_login import current_user

from app import create_app
from app.extensions import db
from app.models import User, Course, TeacherRequest
from app.decorators import role_required, is_owner


@pytest.fixture
def app():

    app = create_app()

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SECRET_KEY="test-secret-key",
    )

    with app.app_context():

        db.create_all()

        @app.route("/admin-only")
        @role_required("admin")
        def admin_only():
            return "OK"

        @app.route("/teacher-only")
        @role_required("teacher")
        def teacher_only():
            return "OK"

        @app.route("/teacher-request", methods=["GET", "POST"])
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

        db.session.add_all([
            admin,
            teacher,
            other_teacher,
            student,
        ])

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