from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_github import GitHub

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('default.cfg')
app.config.from_pyfile('application.cfg', silent=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
github = GitHub(app)

from controller
from model import User, Vm, Removed
