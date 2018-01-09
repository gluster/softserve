from flask import render_template, url_for, request, session, g, jsonify, redirect, url_for
from sqlalchemy import func, desc
import argparse

from softserve import app, db, github
from model import User, Node_request
from lib import *

@app.before_request
def before_request():
    print "hii"
    g.user = None
    if 'token' in session:
        user = User.query.filter_by(token=session['token']).first()
        g.user = user

@github.access_token_getter
def token_getter():
    return session['token']

@app.route('/', methods=['GET', 'POST'])
def about():
    return render_template('about.html') #starting page

@app.route('/login', methods=['GET', 'POST'])
def login():
    print "check"
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

    return  redirect('/home')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/create-node', methods=['POST'])
@organization_access_required('gluster')
def get_node_data():

    if request.method == 'POST':
        node_counts = request.form['counts']
        node_name = request.form['node_name']
        hours = request.form['hours']
        pubkey = request.form['pubkey']
        node_request = Node_request(node_name, node_counts, hours, pubkey)
        db.session.add(node_request)
        db.session.commit()

        session['node_request_id'] = node_request.id

        create_node(node_counts, node_name)
        return redirect('/')
