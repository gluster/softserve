from flask import render_template, redirect, request, session, g, flash  # noqa: E50
from sqlalchemy import func
from sshpubkeys import SSHKey, exceptions
import logging
import re
import requests

from softserve import app, db, github
from model import User, NodeRequest, Vm
from lib import create_node, organization_access_required, delete_node


@app.before_request
def before_request():
    g.user = None
    if 'token' in session:
        user = User.query.filter_by(token=session['token']).first()
        g.user = user


@github.access_token_getter
def token_getter():
    return session['token']


@app.route('/', methods=['GET', 'POST'])
def about():
    if 'token' in session:
        return redirect('/dashboard')
    else:
        return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return github.authorize(scope="read:org")


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    session['token'] = access_token
    if access_token:
        user_data = github.get('user')
        user = User.query.filter_by(username=user_data['login']).first()

        # retreive key from github account
        key = requests.get('https://github.com/%s.keys'
                           % user_data['login'])
        pubkey_ = str((key.text))

        if user is None:
            user = User()
            db.session.add(user)
            user.username = user_data['login']
            user.token = access_token
            user.email = user_data['email']
            user.name = user_data['name']
            user.pubkey = pubkey_
            db.session.commit()
        else:
            user.token = access_token
            user.pubkey = pubkey_
            db.session.commit()
        return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/dashboard', methods=['GET', 'POST'])
@organization_access_required('gluster')
def dashboard():
    vms = Vm.query.filter(NodeRequest.user_id == g.user.id,
                          Vm.state == 'running') \
          .join(NodeRequest).join(User).all()
    admins = app.config['ADMINS']
    return render_template('dashboard.html', vms=vms, admins=admins)


@app.route('/create', methods=['GET', 'POST'])
@organization_access_required('gluster')
def get_node_data():
    count = db.session.query(func.count(Vm.id)) \
        .filter_by(state='running').scalar()
    n = (5-count)
    user = User.query.filter_by(username=g.user.username).first()

    if request.method == "POST":
        counts = request.form['counts']
        name = request.form['node_name']
        hours_ = request.form['hours']
        key = request.form['pubkey']

        # Validating the hours and node counts
        if int(counts) > 5 or int(hours_) > 4 or int(counts) > n:
            flash('Please enter the valid data')
            logging.exception('User entered the invalid hours or counts value')
            return render_template('form.html', n=n, pubkey=user.pubkey)

        # checking if key is changed by user or not
        if key != user.pubkey:
            public_key = key
            # Validating the new SSH public key
            ssh = SSHKey(public_key, strict=True)
            try:
                ssh.parse()
            except (exceptions.InvalidKeyError, exceptions.MalformedDataError):
                logging.exception('Invalid or no key is passed')
                flash('Please upload a valid SSH key')
                return render_template('form.html', n=n, pubkey=user.pubkey)
        else:
            public_key = user.pubkey

        # Validating the machine label
        label = Vm.query.filter(Vm.state == 'running',
                                NodeRequest.node_name == name). \
            join(NodeRequest).first()
        if label is None:
            if re.match("^[a-zA-Z0-9_]+$", str(name)):
                node_request = NodeRequest(
                    user_id=g.user.id,
                    node_name=name,
                    node_counts=counts,
                    hours=hours_)
                db.session.add(node_request)
                db.session.commit()
                create_node.delay(counts, name, node_request.id, public_key)
                flash('Creating your machine. Please wait for a moment.')
                return redirect('/dashboard')
            else:
                flash('Invalid label entry.')
        else:
            flash('Machine label already exists.'
                  'Please choose different name.')
    else:
        if count >= 5:
            flash('All our available machines are in use.'
                  'Please wait until we have a slot available')
            return redirect('/dashboard')
        else:
            flash('You can request upto {} machines'.format(n))
    return render_template('form.html', n=n, pubkey=user.pubkey)


@app.route('/delete-node/<int:vid>')
@app.route('/delete-node')
@organization_access_required('gluster')
def delete(vid=None):
    if vid is None:
        vms = Vm.query.filter(NodeRequest.user_id == g.user.id,
                              Vm.state == 'running') \
              .join(NodeRequest).join(User).all()

        for m in vms:
            name = str(m.vm_name)
            delete_node.delay(name)
            flash('Deleting {} machine'.format(name))
    else:
        machine = Vm.query.filter_by(id=vid).first()
        name = str(machine.vm_name)
        delete_node.delay(name)
        flash('Deleting {} machine'.format(name))
    return redirect('/dashboard')


@app.route('/report')
def report():
    request = NodeRequest.query.filter(NodeRequest.user_id == User.id).\
                                join(User).all()
    data = {}
    for r in request:
        vm = Vm.query.filter(Vm.details_id == r.id).join(NodeRequest).all()
        data[str(r.user.name)] = vm
    print data
    return render_template('report.html', detail=data)
