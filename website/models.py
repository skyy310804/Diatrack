from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):

    

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(
    db.String(50),
    default="avatar1.png"
    )
    last_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    basal_rate = db.Column(db.Float, default=1.0)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    # New Profile Fields
    birthday = db.Column(db.Date, nullable=True)

    gender = db.Column(db.String(20), nullable=True)

        
    glucose_logs = db.relationship(
        "Glucose",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    carb_logs = db.relationship(
        "Carbs",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    insulin_logs = db.relationship(
        "Insulin",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Glucose(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    glucose_level = db.Column(db.Integer)

    recorded_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )


class Carbs(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    carbs = db.Column(db.Integer)

    meal = db.Column(db.String(100))

    recorded_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )


class Insulin(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    units = db.Column(db.Float)

    insulin_type = db.Column(db.String(100))

    recorded_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )
    