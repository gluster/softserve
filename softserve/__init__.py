import pyrax
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_github import GitHub

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('default.cfg')
app.config.from_pyfile('application.cfg', silent=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
github = GitHub(app)
Bootstrap(app)

#pyrax.set_setting('identity_type', app.config['AUTH_SYSTEM'])
#pyrax.set_default_region(app.config['AUTH_SYSTEM_REGION '])
#pyrax.set_credentials(app.config['USERNAME'], app.config['PASSWORD'])
nova = pyrax.cloudservers

from views import about

db.create_all()
