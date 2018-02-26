from flask import render_template, redirect, request, session, g, flash  # noqa: E50
from sqlalchemy import func
from sshpubkeys import SSHKey, exceptions
import logging


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

        if user is None:
            user = User()
            db.session.add(user)
            user.username = user_data['login']
            user.token = access_token
            user.email = user_data['email']
            user.name = user_data['name']
            db.session.commit()
        else:
            user.token = access_token
            db.session.commit()
        return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    vms = Vm.query.filter(NodeRequest.user_id == g.user.id,
                          Vm.state == 'ACTIVE') \
          .join(NodeRequest).join(User).all()
    return render_template('dashboard.html', vms=vms)


@app.route('/create_node', methods=['GET', 'POST'])
@organization_access_required('gluster')
def get_node_data():
    if request.method == "POST":
        counts = request.form['counts']
        name = request.form['node_name']
        hours_ = request.form['hours']
        pubkey_ = request.form['pubkey']

        count = db.session.query(func.count(Vm.id)) \
            .filter_by(state='ACTIVE').scalar()
        n = (5-count)

        # Validating the hours and node counts
        if counts > 5 or hours_ > 4:
            flash('Please enter the valid data')
            logging.exception('User entered the invalid hours or counts value')
            return render_template('form.html', n=n)

        # Validating the SSH public key
        ssh = SSHKey(pubkey_, strict=True)
        try:
            ssh.parse()
        except (exceptions.InvalidKeyError, exceptions.MalformedDataError):
            logging.exception('Invalid key is passed')
            flash('Invalid SSH key')
            return render_template('form.html', n=n)

        # Validating the machine label
        n = NodeRequest.query.filter_by(node_name=name).first()
        if n is None:
            node_request = NodeRequest(
                user_id=g.user.id,
                node_name=name,
                node_counts=counts,
                hours=hours_,
                pubkey=pubkey_)
            db.session.add(node_request)
            db.session.commit()
            create_node.delay(counts, name, node_request.id, pubkey_)
            flash('Creating your machine. Please wait for a moment.')
            return redirect('/dashboard')
        else:
            flash('Machine label already exists.'
                  'Please choose different name.')
    else:
        count = db.session.query(func.count(Vm.id)) \
                .filter_by(state='ACTIVE').scalar()
        if count >= 5:
            flash('All our available machines are in use.'
                  'Please wait until we have a slot available')
            return redirect('/dashboard')
        else:
            n = (5-count)
            flash('You can request upto {} machines'.format(n))
    return render_template('form.html', n=n)


@app.route('/delete-node/<int:vid>')
@app.route('/delete-node')
@organization_access_required('gluster')
def delete(vid=None):
    if vid is None:
        vms = Vm.query.filter(NodeRequest.user_id == g.user.id,
                              Vm.state == 'ACTIVE') \
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
