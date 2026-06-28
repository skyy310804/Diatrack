from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

from .models import User
from . import db

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("views.home"))

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(email=email).first()

        if user:

            if check_password_hash(user.password, password):

                login_user(user, remember=remember)

                flash("Welcome back!", "success")

                return redirect(url_for("views.home"))

            else:

                flash("Incorrect password.", "danger")

        else:

            flash("Account does not exist.", "danger")

    return render_template("login.html")


@auth.route("/sign-up", methods=["GET", "POST"])
def sign_up():

    if current_user.is_authenticated:
        return redirect(url_for("views.home"))

    if request.method == "POST":

        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        user = User.query.filter_by(email=email).first()

        if user:

            flash("Email already exists.", "danger")

        elif len(first_name) < 2:

            flash("First name is too short.", "danger")

        elif len(last_name) < 2:

            flash("Last name is too short.", "danger")

        elif password1 != password2:

            flash("Passwords do not match.", "danger")

        elif len(password1) < 6:

            flash("Password must be at least 6 characters.", "danger")

        else:

            new_user = User(

                first_name=first_name,
                last_name=last_name,
                email=email,
                password=generate_password_hash(
                    password1,
                    method="pbkdf2:sha256"
                )

            )

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)

            flash("Account created successfully!", "success")

            return redirect(url_for("views.home"))

    return render_template("sign_up.html")


@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))