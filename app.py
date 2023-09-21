from flask import Flask, flash, render_template, request, session, redirect
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import secrets


app = Flask(__name__)
app.debug = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app_tracker.db"
app.config["SESSION_PERMANENT"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = secrets.token_hex(32)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    opps = db.relationship("Opportunity", back_populates="user")
    tasks = db.relationship("Task", back_populates="user")
    materials = db.relationship("Material", back_populates="user")
    links = db.relationship("Link", back_populates="user")
    applications = db.relationship("Application_History", back_populates="user")


class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_name = db.Column(db.String(255))
    title = db.Column(db.String(255))
    app_deadline = db.Column(db.DateTime)
    personal_deadline = db.Column(db.DateTime)
    requirements = db.Column(db.String(255))
    link = db.Column(db.String(255))
    short_description = db.Column(db.TEXT)
    category = db.Column(db.String(255))
    priority = db.Column(db.Integer)
    status = db.Column(db.String(255))
    notes = db.Column(db.DateTime)
    other_info = db.Column(db.DateTime)
    contact_info = db.Column(db.DateTime)
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship("User", back_populates="opps")
    materials = db.relationship("Material", back_populates="opps")
    tasks = db.relationship("Task", back_populates="opps")
    applications = db.relationship("Application_History", back_populates="opps")


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    opp_id = db.Column(db.Integer, db.ForeignKey(Opportunity.id))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    status = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    user = db.relationship("User", back_populates="tasks")
    opps = db.relationship("Opportunity", back_populates="tasks")


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    file = db.Column(db.String(255))
    opp_id = db.Column(db.Integer, db.ForeignKey(Opportunity.id))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    user = db.relationship("User", back_populates="materials")
    opps = db.relationship("Opportunity", back_populates="materials")


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    link = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    user = db.relationship("User", back_populates="links")


class Application_History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_date = db.Column(db.DateTime, default=db.func.utcnow)
    opp_id = db.Column(db.Integer, db.ForeignKey(Opportunity.id))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    user = db.relationship("User", back_populates="applications")
    opps = db.relationship("Opportunity", back_populates="applications")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        # add to table op
        redirect("/")
    return render_template("addOp.html")


@app.route("/calendar")
@login_required
def calendar():
    # send the events as list of dictionaries
    # title, startDate, color
    return render_template("calendar.html")


@app.route("/history")
@login_required
def history():
    # send history
    return render_template("history.html")


@app.route("/links", methods=["POST"])
@login_required
def links():
    # add link to table
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            # return apology("must provide username", 403)
            return redirect("/")

        # Ensure password was submitted
        elif not request.form.get("password"):
            # return apology("must provide password", 403)
            return redirect("/")

        # Query database for username
        user = User.query.filter_by(username=request.form.get("username")).first()

        # Ensure username exists and password is correct
        if not user or not check_password_hash(
            user.password, request.form.get("password")
        ):
            return redirect("/")

        # Remember which user has logged in
        session["user_id"] = user.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/materials", methods=["POST"])
@login_required
def materials():
    # add material to table
    return redirect("/")


@app.route("/notes")
@login_required
def notes():
    # send notes
    return render_template("notes.html")


@app.route("/profile")
@login_required
def profile():
    # send current user's profile
    return render_template("profile.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        return redirect("/")
    return render_template("register.html")


@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    if request.method == "POST":
        # add tasks to table
        return redirect("/")
    return render_template("tasks.html")


# make this based on id
@app.route("/view")
@login_required
def view():
    # send the data corresponding to op: op, tasks, materials,
    return render_template("viewOp.html")


# task(POST), material(POST), op(GET, POST), user (GET, POST), link(POST), history(GET)
