from flask import render_template, redirect, request, session, g, flash, jsonify

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
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return github.authorize(scope="read:org")


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    print(access_token)
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


@app.route('/form', methods=['GET', 'POST'])
def home():
    count = db.session.query(func.count(Vm.id)).scalar()
    if count == 5:
        flash('You are in Queue. Try again later')
    else:
        (5-count) = n
        flash('You can request upto {} machines').format(n)
    return render_template('home.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    vms = Vm.query.filter(NodeRequest.user_id == g.user.id,
                          Vm.state == 'ACTIVE') \
          .join(NodeRequest).join(User).all()
    print(vms)
    if vms == []:
        flash('No records found')
    return render_template('dashboard.html', vms=vms)


@app.route('/create_node', methods=['GET', 'POST'])
# @organization_access_required('gluster')
def get_node_data():
    if request.method == "POST":
        counts = request.form['counts']
        name = request.form['node_name']
        hours_ = request.form['hours']
        pubkey_ = request.form['pubkey']
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
            create_node(counts, name, node_request, pubkey_)
            flash('Your VM has been created. Go back to Dashboard')
        else:
            flash('Machine label already exists. Please choose different name.')
    return redirect('/form')


@app.route('/delete-node/<int:vid>')
@app.route('/delete-node')
# @organization_access_required('gluster')
def delete(vid=None):
    if vid is None:
        vms = Vm.query.filter(NodeRequest.user_id == g.user.id,
                              Vm.state == 'ACTIVE') \
              .join(NodeRequest).join(User).all()

        for m in vms:
            name = str(m.vm_name)
            delete_node(name)
            m.state = 'DELETED'
            db.session.commit()
    else:
        machine = Vm.query.filter_by(id=vid).first()
        name = str(machine.vm_name)
        delete_node(name)
        machine.state = 'DELETED'
        db.session.commit()
    return redirect('/dashboard')
