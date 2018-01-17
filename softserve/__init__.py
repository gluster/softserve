from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_github import GitHub
from apscheduler.scheduler import Scheduler

from views import about
from model import User, Node_request, Vm
from task import shutdown_check

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('default.cfg')
app.config.from_pyfile('application.cfg', silent=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
github = GitHub(app)
scheduler = Scheduler()
scheduler.start()
scheduler.add_cron_job(shutdown_check, minute='*/5')

db.create_all()
