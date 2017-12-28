from flask import render_template, url_for, request, session, g, jsonify, redirect, url_for
from sqlalchemy import func, desc
import argparse
import os
import sys
import time
import re
import pyrax

from softserve import app, db, github
from model import User, Vm, Removed
from lib import *

@app.before_request
def before_request():
    g.user = None
    if 'token' in session:
        user = User.query.filter_by(token=session['token'])
        g.user = user

@github.access_token_getter
def token_getter():
    return session['token']

@app.route('/', methods=['GET', 'POST'])
def about():
    return render_template('about.html') #starting page

@app.route('/login', methods=['POST'])
def login():
    if session['username'] is None:
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
            db.session.add(user)
            db.session.commit()
    return  redirect('/home')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/create_node', methods=['POST'])
@organization_access_required('gluster')
def get_node_data():
    pyrax.set_setting('identity_type', app.config['AUTH_SYSTEM'])
    pyrax.set_default_region(app.config['AUTH_SYSTEM_REGION '])
    pyrax.set_credentials(app.config['USERNAME'], app.config['PASSWORD'])
    nova = pyrax.cloudservers

    if request.method == 'POST':
        counts = request.form['counts']
        cluster_name = request.form['cluster_name']
        hours = request.form['hours']
        pubkey = request.form['pubkey']
        vm_details = Vm_details(cluster_name, nodes, hours, pubkey)
        db.session.add(vm_details)
        db.session.commit()

        flavor = nova.flavors.find(name='512MB Standard Instance')
        image = nova.images.find(name='Ubuntu 14.04 LTS (Trusty Tahr)')

        # create the nodes
        for count in range(counts):
            node_name = str(count+1)+'.'+cluster_name
            node = nova.servers.create(name=node_name, flavor=flavor.id, image=image.id, key_name=pubkey)

            # wait for server create to be complete
            while node.status == 'BUILD':
                time.sleep(5)
                node = nova.servers.get(server.id)

            #get ip_address of the node
            for network in node.networks['public']:
                if re.match('\d+\.\d+\.\d+\.\d+', network):
                    ip_address = network
                    f = open(cluster_name, 'a')
                    f.write("{}\n".format(ip_address))
                    f.close()
        return redirect('/')
