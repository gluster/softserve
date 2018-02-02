from flask import render_template, url_for, request, session, g, redirect, jsonify

from softserve import app, db, github
from model import User, Node_request, Vm
from lib import create_node, organization_access_required


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

            session['user_id'] = user.id
    return redirect('/home')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')


@app.route('/create-node', methods=['GET', 'POST'])
#@organization_access_required('gluster')
def get_node_data():
    if request.method == 'POST':
        print g.user
        print session
        counts = request.form['counts']
        name = request.form['node_name']
        hours_ = request.form['hours']
        pubkey_ = request.form['pubkey']
        purpose_ = request.form['purpose']
        node_request = Node_request(user_id=g.user.id, node_name=name, node_counts=counts, hours=hours_, pubkey=pubkey_, purpose=purpose_)
        db.session.add(node_request)
        db.session.commit()

        session['node_request_id'] = node_request.id

        create_node(counts, name, node_request, pubkey_)
    return jsonify({"response": "success"})

    #@app.route('/delete-node', methods=['GET'])
    #def
