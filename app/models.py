from flask_login import UserMixin

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )


course_students = db.Table(
    "course_students",
    db.metadata,
    db.Column(
        "course_id",
        db.Integer,
        db.ForeignKey("dbo.courses.id"),
        primary_key=True
    ),
    db.Column(
        "student_id",
        db.Integer,
        db.ForeignKey("dbo.users.id"),
        primary_key=True
    ),
    schema="dbo"
)


class Course(db.Model):
    __tablename__ = "courses"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.String(500)
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("dbo.users.id"),
        nullable=False
    )

    teacher = db.relationship(
        "User",
        backref="courses"
    )

    students = db.relationship(
        "User",
        secondary=course_students,
        backref="enrolled_courses"
    )

    topics = db.relationship(
        "Topic",
        back_populates="course",
        cascade="all, delete-orphan"
    )


class Topic(db.Model):
    __tablename__ = "topics"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("dbo.courses.id"),
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.String(500)
    )

    course = db.relationship(
        "Course",
        back_populates="topics"
    )


class Material(db.Model):
    __tablename__ = "materials"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    topic_id = db.Column(
        db.Integer,
        db.ForeignKey("dbo.topics.id"),
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    file_type = db.Column(
        db.String(100)
    )

    topic = db.relationship(
        "Topic",
        backref="materials"
    )

class TeacherRequest(db.Model):
    __tablename__ = "teacher_requests"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("dbo.users.id"),
        nullable=False
    )

    experience = db.Column(
        db.Text,
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.getdate()
    )

    user = db.relationship(
        "User",
        backref=db.backref("teacher_requests", lazy=True)
    )