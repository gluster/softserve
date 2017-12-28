from softserve import db
from datetime import datetime

class User(db.model):
        #__tablename__ = 'Users'
        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        username = db.Column(db.String(100), unique=True, nullable=False)
        token = db.Column(db.String(1000))
        email = db.Column(db.String(100), unique=True)
        name = db.Column(db.String(100))

class Vm_details(db.model):
    #__tablename__ = 'Vms_details'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cluster_name = db.Column(db.String(100), unique=True, nullable=False)
    nodes = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    pubkey = db.Column(db.varchar(1024), nullable=False)
    vms = db.relationship('Vm', backref=db.backref('Users'), lazy='dynamic')
    def as_dict(self):
        return{
        "cluster_name" = self.cluster_name,
        "nodes" = self.nodes,
        "hours" = self.hours
        }

class Vm(db.model):
    #__tablename__ = 'Vms'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.varchar(45), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    details_id = db.Column(db.Integer, db.ForeignKey('Vms_details.id'))
    created_at = db.Column(db.DateTime)
    state = db.Column(db.String(10))
    def __init__(self, ip_address, created_at, state):
        self.ip_address = ip_address
        self.created_at = datetime.now()
        self.state = state

class Removed(db.model):
    #__tablename__ = 'Removed_vms'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    delete_id = db.Column(db.Integer, db.ForeignKey('Vms.id'))
    deleted_at = db.Column(db.DateTime)
    def __init__(self, deleted_at):
        self.deleted_at = datetime.now()
