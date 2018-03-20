from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_github import GitHub
from celery import Celery

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('default.cfg')
app.config.from_pyfile('application.cfg', silent=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
github = GitHub(app)
Bootstrap(app)
celery = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'],
                broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


from views import about  # noqa: E402, F401
from model import User, NodeRequest, Vm  # noqa: E402, F401
<<<<<<< c83a1dd433f7fede5bf63113f387a3a4b3e4032e
<<<<<<< d9efd336f3872be8f153d58d949a089f61376283
=======

# db.create_all()
>>>>>>> Create a new migration for a change in Vm table
=======
>>>>>>> Remove commented lines and add message in version file
