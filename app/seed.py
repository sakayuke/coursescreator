from werkzeug.security import generate_password_hash

from .extensions import db
from .models import User


def create_test_users():
    users = [
        ("Test", "Admin", "admin@test.com", "admin"),
        ("Test", "Teacher", "teacher@test.com", "teacher"),
        ("Test", "Student", "student@test.com", "student"),
    ]

    created = 0

    for first_name, last_name, email, role in users:
        if User.query.filter_by(email=email).first():
            print(f"{email} already exists")
            continue

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=generate_password_hash("123456"),
            role=role
        )

        db.session.add(user)
        created += 1

    db.session.commit()

    print(f"Created {created} test users.")