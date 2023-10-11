import os
import json
from flask import Flask, flash, render_template, request, session, redirect
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_session import Session
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import secrets


app = Flask(__name__)
app.debug = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app_tracker.db"
app.config["UPLOAD_EXTENSIONS"] = [".jpg", ".png", ".gif", "pdf"]
app.config["SESSION_PERMANENT"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = secrets.token_hex(32)
app.static_folder = "static"  # Set the static folder to 'static'
app.static_url_path = "/static"


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    opps = db.relationship("Opportunity", cascade="all, delete", back_populates="user")
    tasks = db.relationship("Task", cascade="all, delete", back_populates="user")
    materials = db.relationship(
        "Material", cascade="all, delete", back_populates="user"
    )
    links = db.relationship("Link", cascade="all, delete", back_populates="user")
    applications = db.relationship(
        "Application_History", cascade="all, delete", back_populates="user"
    )


class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    app_deadline = db.Column(db.String(255))
    personal_deadline = db.Column(db.String(255))
    requirements = db.Column(db.Text)
    link = db.Column(db.String(255))
    short_description = db.Column(db.TEXT)
    category = db.Column(db.String(255))
    priority = db.Column(db.Integer, default=0)
    status = db.Column(db.String(255), default="Haven't Started")
    notes = db.Column(db.Text)
    other_info = db.Column(db.Text)
    contact_info = db.Column(db.Text)
    location = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship("User", back_populates="opps")
    materials = db.relationship(
        "Material", cascade="all, delete", back_populates="opps"
    )
    tasks = db.relationship("Task", cascade="all, delete", back_populates="opps")
    applications = db.relationship(
        "Application_History", cascade="all, delete", back_populates="opps"
    )


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    opp_id = db.Column(db.Integer, db.ForeignKey(Opportunity.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    status = db.Column(db.String(255), default="Not done")
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    user = db.relationship("User", back_populates="tasks")
    opps = db.relationship("Opportunity", back_populates="tasks")


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    file = db.Column(db.String(255), nullable=False)
    opp_id = db.Column(db.Integer, db.ForeignKey(Opportunity.id))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship("User", back_populates="materials")
    opps = db.relationship("Opportunity", back_populates="materials")


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    user = db.relationship("User", back_populates="links")


class Application_History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_date = db.Column(db.Date, default=date.today())
    opp_id = db.Column(db.Integer, db.ForeignKey(Opportunity.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.utcnow)
    user = db.relationship("User", back_populates="applications")
    opps = db.relationship("Opportunity", back_populates="applications")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    status = request.form.get("status")
    category = request.form.get("category")
    sort_by = request.form.get("sort")

    query = Opportunity.query
    if sort_by == "app_deadline":
        query = query.filter(Opportunity.user_id == session["user_id"]).order_by(
            Opportunity.app_deadline.desc()
        )
    elif sort_by == "personal_deadline":
        query = query.filter(Opportunity.user_id == session["user_id"]).order_by(
            Opportunity.personal_deadline.desc()
        )

    else:
        query = query.filter(Opportunity.user_id == session["user_id"])

    if status and status != "all":
        query = query.filter(Opportunity.status == status)

    if category and category != "all":
        query = query.filter(Opportunity.category == category)

    opportunities = query.all()

    return render_template("index.html", opps=opportunities)


@app.route("/apply", methods=["POST"])
@login_required
def apply():
    application = Application_History(
        opp_id=request.form.get("opp_id"),
        user_id=session["user_id"],
        application_date=datetime.now(),
        created_at=datetime.now(),
    )
    db.session.add(application)
    db.session.commit()
    opp = Opportunity.query.filter(
        (Opportunity.id == application.opp_id)
        & (Opportunity.user_id == session["user_id"])
    ).first()
    opp.status = "Applied"
    db.session.commit()
    return redirect("/history")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        # add to table op
        new_opp = Opportunity(
            org_name=request.form.get("org_name"),
            title=request.form.get("title"),
            app_deadline=request.form.get("app_deadline"),
            personal_deadline=request.form.get("personal_deadline"),
            requirements=request.form.get("requirements"),
            category=request.form.get("category"),
            link=request.form.get("link"),
            short_description=request.form.get("short_description"),
            priority=request.form.get("priority"),
            status=request.form.get("status"),
            notes=request.form.get("notes"),
            other_info=request.form.get("other_info"),
            contact_info=request.form.get("contact_info"),
            location=request.form.get("location"),
            created_at=datetime.now(),
            user_id=session["user_id"],
        )
        db.session.add(new_opp)
        db.session.commit()
        if new_opp.status == "Applied":
            application = Application_History(
                opp_id=request.form.get("opp_id"),
                user_id=session["user_id"],
                application_date=datetime.now(),
                created_at=datetime.now(),
            )
            db.session.add(application)
            db.session.commit()
        value = request.form.get("tasks")
        tasks = value.split(",")
        for task in tasks:
            task = task.strip().capitalize()
            new_task = Task(
                user_id=session["user_id"],
                opp_id=new_opp.id,
                description=task,
                created_at=datetime.now(),
            )
            db.session.add(new_task)
            db.session.commit()

        # task logic

        return redirect("/")
    return render_template("addOp.html")


@app.route("/calendar")
@login_required
def calendar():
    # send the events as list of dictionaries
    # title, startDate, color
    # title, app_deadline AND #title, personal_deadline
    opps = db.session.execute(
        text(
            "SELECT title, org_name, app_deadline, personal_deadline FROM Opportunity WHERE user_id = :user_id"
        ),
        {"user_id": session["user_id"]},
    )
    events = []
    for opp in opps:
        # val 1 and 2 are dicts
        val1 = {}
        val2 = {}
        # disect array to include title, app_deadline, color AND  title, personal_deadline, color
        # then append all into the new array
        val2["title"] = val1["title"] = opp.title + ", " + opp.org_name
        val1["start"] = opp.app_deadline
        val1["color"] = "red"
        val2["start"] = opp.personal_deadline
        val2["color"] = "blue"
        events.append(val1)
        events.append(val2)
        # append to the array

    return render_template("calendar.html", events=events)


@app.route("/history")
@login_required
def history():
    # send history
    apps = db.session.execute(
        text(
            "SELECT Opportunity.title, Application__History.application_date, Opportunity.org_name, Opportunity.link, Application__History.opp_id FROM Application__History JOIN Opportunity ON Application__History.opp_id = Opportunity.id WHERE Application__History.user_id = :user_id"
        ),
        {"user_id": session["user_id"]},
    )
    return render_template("history.html", apps=apps)


@app.route("/links", methods=["POST"])
@login_required
def links():
    # add link to table
    new_link = Link(
        user_id=session["user_id"],
        title=request.form.get("title"),
        link=request.form.get("link"),
        created_at=datetime.now(),
    )

    db.session.add(new_link)
    db.session.commit()
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
        session["user_name"] = user.username

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
    uploaded_file = request.files["file"]
    if uploaded_file:
        if (
            uploaded_file.filename.rsplit(".", 1)[1].lower()
            not in app.config["UPLOAD_EXTENSIONS"]
        ):
            return "Invalid file extension."

        uploaded_file.save("files")
        new_material = Material(
            user_id=session["user_id"],
            opp_id=request.form.get("id"),
            file="files/" + uploaded_file.filename,
            title=request.form.get("title"),
            created_at=datetime.now(),
        )
        db.session.add(new_material)
        db.session.commit()
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
    user = User.query.filter_by(id=session["user_id"]).first()
    links = Link.query.filter_by(user_id=session["user_id"]).all()
    materials = Material.query.filter_by(user_id=session["user_id"]).all()

    return render_template("profile.html", materials=materials, links=links, user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            flash("Must provide username")
            return
        new_user = User.query.filter_by(username=request.form.get("username")).first()
        if new_user:
            flash("Username is already taken")
            return
            # return apology("Username is already taken")
        if not request.form.get("password") or not request.form.get("confirm"):
            flash("Must provide password")
            return
        if request.form.get("password") != request.form.get("confirm"):
            flash("Passwords don't match")
            return
        user = User(
            name=request.form.get("name"),
            email=request.form.get("email"),
            username=request.form.get("username"),
            password=generate_password_hash(request.form.get("password")),
            created_at=datetime.now(),
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered!")
        return redirect("/")
    return render_template("register.html")


@app.route("/add/task", methods=["POST"])
@login_required
def add_tasks():
    # add tasks to table
    description = request.form.get("desc")
    desc = description.strip()

    new_task = Task(
        user_id=session["user_id"],
        opp_id=request.form.get("id"),
        description=desc.capitalize(),
        created_at=datetime.now(),
    )

    db.session.add(new_task)
    db.session.commit()
    return redirect("/")
    # add opportunity names to before sending


@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    filter_option = request.form.get("filter")
    if filter_option == "done":
        tasks = db.session.execute(
            text(
                "SELECT Opportunity.title, Task.description, Task.status, Task.opp_id FROM Task JOIN Opportunity ON Task.opp_id = Opportunity.id WHERE Task.user_id = :user_id AND Task.status = 'Done'"
            ),
            {"user_id": session["user_id"]},
        )
    elif filter_option == "not done":
        tasks = db.session.execute(
            text(
                "SELECT Opportunity.title, Task.description, Task.status, Task.opp_id FROM Task JOIN Opportunity ON Task.opp_id = Opportunity.id WHERE Task.user_id = :user_id AND Task.status = 'Not Done'"
            ),
            {"user_id": session["user_id"]},
        )
    else:
        # add opportunity names to before sending
        tasks = db.session.execute(
            text(
                "SELECT Opportunity.title, Task.description, Task.status, Task.opp_id FROM Task JOIN Opportunity ON Task.opp_id = Opportunity.id WHERE Task.user_id = :user_id"
            ),
            {"user_id": session["user_id"]},
        )
    return render_template("tasks.html", tasks=tasks)


@app.route("/update_status", methods=["POST"])
def update_status():
    id = request.form.get("id")
    status = request.form.get("status")

    task = Task.query.get_or_404(id)
    task.status = "Done" if status == "true" else "Not Done"

    db.session.commit()
    return redirect("/")


# make this based on id
@app.route("/view/<int:opp_id>")
@login_required
def view(opp_id):
    opp = Opportunity.query.filter(
        (Opportunity.user_id == session["user_id"]) & (Opportunity.id == opp_id)
    ).first()
    tasks = Task.query.filter(
        (Task.user_id == session["user_id"]) & (Task.opp_id == opp_id)
    ).all()
    materials = Material.query.filter(
        (Material.user_id == session["user_id"]) & (Material.opp_id == opp_id)
    ).all()

    if Application_History.query.filter(
        (Application_History.user_id == session["user_id"])
        & (Application_History.opp_id == opp_id)
    ).first():
        applied = True
    else:
        applied = False
    # send the data corresponding to op: op, tasks, materials,
    return render_template(
        "viewOp.html", opp=opp, tasks=tasks, materials=materials, applied=applied
    )


# task(POST), material(POST), op(GET, POST), user (GET, POST), link(POST), history(GET)
@app.route("/op/edit/<int:id>", methods=["POST"])
@login_required
def update_op(id):
    op = Opportunity.query.get_or_404(id)
    op.org_name = (request.form.get("org_name"),)
    op.title = (request.form.get("title"),)
    op.app_deadline = (request.form.get("app_deadline"),)
    op.personal_deadline = (request.form.get("personal_deadline"),)
    op.requirements = (request.form.get("requirements"),)
    op.category = (request.form.get("category"),)
    op.link = (request.form.get("link"),)
    op.short_description = (request.form.get("short_description"),)
    op.priority = (request.form.get("priority"),)
    op.status = (request.form.get("status"),)
    op.notes = (request.form.get("notes"),)
    op.other_info = (request.form.get("other_info"),)
    op.contact_info = (request.form.get("contact_info"),)
    op.location = (request.form.get("location"),)
    db.session.commit()
    if op.status == "Applied":
        application = Application_History(
            opp_id=id,
            user_id=session["user_id"],
            application_date=datetime.now(),
            created_at=datetime.now(),
        )
        db.session.add(application)
        db.session.commit()
    return redirect("/")


@app.route("/link/edit", methods=["POST"])
@login_required
def edit_link():
    id = request.form.get("id")
    link = Link.query.get_or_404(id)
    link.title = request.form.get("edit_title")
    link.link = request.form.get("edit_link")
    db.session.commit()
    return redirect("/")


@app.route("/material/edit", methods=["POST"])
@login_required
def edit_material():
    id = request.form.get("id")
    material = Material.query.get_or_404(id)
    material.title = request.form.get("edit_file_title")
    if request.form.get("file"):
        material.file = request.form.get("file")
    db.session.commit()
    return redirect("/")


@app.route("/edit", methods=["POST"])
def edit_profile():
    user = User.query.get_or_404(session["user_id"])
    user.name = request.form.get("name")
    user.email = request.form.get("email")
    user.username = request.form.get("username")
    db.session.commit()
    return redirect("/")


@app.route("/op/<int:id>/delete", methods=["POST"])
def delete_op(id):
    op = Opportunity.query.get_or_404(id)
    db.session.delete(op)
    db.session.commit()
    return redirect("/")


@app.route("/material/<int:id>/delete", methods=["POST"])
def delete_material(id):
    op = Material.query.get_or_404(id)
    db.session.delete(op)
    db.session.commit()
    return redirect("/")


@app.route("/link/<int:id>/delete", methods=["POST"])
def delete_link(id):
    op = Link.query.get_or_404(id)
    db.session.delete(op)
    db.session.commit()
    return redirect("/")
