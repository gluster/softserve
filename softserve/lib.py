import pyrax
import os
import sys
import time
import re
from datetime import datetime
from functools import wraps
from softserve import app, db, github
from model import Vm
from flask import jsonify

def organization_access_required(org):
    """
    Decorator that can be used to validate the presence of user in a particular organization.
    """
    def decorator(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            orgs = github.get('user/orgs')
            for org_ in orgs:
                if org_['login'] == org:
                    return func(*args, **kwargs)
            return jsonify({"response": "You must be the member of gluster \
                           organization on Github to serve yourself machines for testing"}), 401
        return wrap
    return decorator

def create_node(counts, name):
    pyrax.set_setting('identity_type', app.config['AUTH_SYSTEM'])
    pyrax.set_default_region(app.config['AUTH_SYSTEM_REGION '])
    pyrax.set_credentials(app.config['USERNAME'], app.config['PASSWORD'])
    nova = pyrax.cloudservers

    flavor = nova.flavors.find(name='') #2048MB
    image = nova.images.find(name='') #CentOS7

    # create the nodes
    for count in range(counts):
        node_name = str(count+1)+'.'+name
        node = nova.servers.create(name=node_name, flavor=flavor.id, image=image.id, key_name=pubkey)

        # wait for server to get active
        while node.status == 'BUILD':
            time.sleep(5)
            node = nova.servers.get(server.id)

        #get ip_address of the node
        for network in node.networks['public']:
            if re.match('\d+\.\d+\.\d+\.\d+', network):
                ip_address = network
                user_id = session['user_id']
                details_id = session['node_request_id']
                created_at = datetime.datetime.now()
                state = node.status
                vm = Vm(ip_address, user_id, details_id, created_at, state)
                db.session.add(vm)
                db.session.commit()
                '''
                Storing the IP address of the machines in a file(filename is same
                as that of the node name given by user) for future purpose
                '''
                f = open(name, 'a')
                f.write("{}\n".format(ip_address))
                f.close()

def delete_node(node_name):
    node = nova.servers.find(name=node_name)
    node.delete()

def sleep_time(hours):
    """
    Decorator that can be used to remove vm after a specific hours
    """
    def decorator(func):
        @wraps(func)
        def wrap(*args, *kwargs):
