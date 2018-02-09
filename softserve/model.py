'''
All the models for softserve go here
'''
from datetime import datetime
from softserve import db


class User(db.Model):
    '''
    User model
    '''
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    token = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    node_request = db.relationship(
        'NodeRequest',
        backref='user',
        lazy='dynamic'
    )

    def __repr__(self):
        return '<user {}>'.format(self.username)


class NodeRequest(db.Model):
    __tablename__ = 'node_request'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    node_name = db.Column(db.String(100), unique=True, nullable=False)
    node_counts = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    pubkey = db.Column(db.VARCHAR(1024), nullable=False)
    vms = db.relationship('Vm', backref='details', lazy='dynamic')

    def as_dict(self):
        return {
            "node_name": self.node_name,
            "node_counts": self.node_counts,
            "hours": self.hours
        }


class Vm(db.Model):
    __tablename__ = 'vm'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.VARCHAR(45))
    vm_name = db.Column(db.String(100), unique=True, nullable=False)
    details_id = db.Column(db.Integer, db.ForeignKey('node_request.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    state = db.Column(db.String(10))

    def __init__(self, ip_address, vm_name, state):
        self.ip_address = ip_address
        self.vm_name = vm_name
        self.created_at = datetime.now()
        self.state = state
