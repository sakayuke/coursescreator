
from flask import render_template
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User


app = create_app()


@app.cli.command("create-admin")
def create_admin():

    email = input("Admin email: ").strip()

    password = input("Admin password: ")

    if not email or not password:

        print("Email and password are required.")

        return

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:

        print("User with this email already exists.")

        return

    user = User(
        first_name="Admin",
        last_name="User",
        email=email,
        password_hash=generate_password_hash(password),
        role="superadmin",
    )

    db.session.add(user)

    db.session.commit()

    print(
        f"Admin {email} created successfully."
    )


@app.route("/")
def home():

    return render_template(
        "home.html"
    )


if __name__ == "__main__":
    app.run(
        debug=True
    )

