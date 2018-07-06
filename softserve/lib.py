'''
Shared library functions for softserve.
'''

import time
import pyrax
import re
import logging
from datetime import datetime
from novaclient.exceptions import NotFound, Conflict
from functools import wraps
from flask import jsonify, g, redirect, url_for, request
from softserve import db, github, celery, app
from softserve.model import Vm, NodeRequest


def organization_access_required(org):
    """
    Decorator that can be used to validate the presence of user in a particular
    organization.
    """
    def decorator(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('login', next=request.url))
            orgs = github.get('user/orgs')
            for org_ in orgs:
                if org_['login'] == org:
                    return func(*args, **kwargs)
            return jsonify({"response": "You must be the member of gluster"
                            " organization on Github to serve"
                            " yourself machines"
                            " for testing"}), 401
        return wrap
    return decorator


@celery.task()
def create_node(counts, name, node_request, pubkey):
    '''
    Create a node in the cloud provider
    '''
    pyrax.set_setting('identity_type', app.config['AUTH_SYSTEM'])
    pyrax.set_default_region(app.config['AUTH_SYSTEM_REGION'])
    pyrax.set_credentials(app.config['USERNAME'], app.config['API_KEY'])
    nova = pyrax.cloudservers

    flavor = nova.flavors.find(name='2 GB General Purpose v1')
    image = nova.images.find(name='centos7-test')
    node_request = NodeRequest.query.get(node_request)
    try:
        nova.keypairs.create(name, pubkey)
    except Conflict:
        logging.exception('Keypair already exist')
    # create the nodes
    for count in range(int(counts)):
        vm_name = 'softserve-'+name+'.'+str(count+1)
        node = nova.servers.create(name=vm_name, flavor=flavor.id,
                                   image=image.id, key_name=name)

        # wait for server to get active
        while node.status == 'BUILD':
            time.sleep(5)
            node = nova.servers.get(node.id)

        # get ip_address of the active node
        for network in node.networks['public']:
            if re.match(r'\d+\.\d+\.\d+\.\d+', network):
                machine = Vm(ip_address=network,
                             vm_name=vm_name,
                             state=node.status)
                machine.details = node_request
                db.session.add(machine)
                db.session.commit()


@celery.task()
def delete_node(vm_name):
    pyrax.set_setting('identity_type', app.config['AUTH_SYSTEM'])
    pyrax.set_default_region(app.config['AUTH_SYSTEM_REGION'])
    pyrax.set_credentials(app.config['USERNAME'], app.config['API_KEY'])
    nova_obj = pyrax.cloudservers
    vm = Vm.query.filter_by(vm_name=vm_name).first()
    try:
        node = nova_obj.servers.find(name=vm_name)
        node.delete()
    except NotFound:
        logging.exception('Server not found')
    vm.state = 'DELETED'
    vm.deleted_at = datetime.now()
    db.session.add(vm)
    db.session.commit()
