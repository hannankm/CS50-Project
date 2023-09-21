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
