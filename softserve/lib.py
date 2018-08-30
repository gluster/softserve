'''
Shared library functions for softserve.
'''

import time
import re
import logging
import socket
from datetime import datetime
from novaclient.exceptions import NotFound, Conflict
from functools import wraps
from flask import jsonify, g, redirect, url_for, request
from softserve import db, github, celery, app
from softserve.model import Vm, NodeRequest
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.deployment import SSHKeyDeployment, MultiStepDeployment


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
    driver = get_driver(Provider.RACKSPACE)
    conn = driver(
            app.config['USERNAME'],
            app.config['API_KEY'],
            region=app.config['AUTH_SYSTEM_REGION']
    )
    flavor = conn.ex_get_size('performance1-2')
    image = conn.get_image('8bca010c-c027-4947-b9c9-adaae6e4f020')

    step = SSHKeyDeployment(pubkey)
    node_request = NodeRequest.query.get(node_request)
    for count in range(int(counts)):
        vm_name = ''.join(['softserve-', name, '.', count+1]
        node = conn.deploy_node(
            name=vm_name, image=image, size=flavor, deploy=step
        )
        for ip in node.public_ips:
            try:
                socket.inet_pton(socket.AF_INET, ip)
                network = ip
            except socket.error
                continue
        machine = Vm(ip_address=network,
                     vm_name=vm_name,
                     state=node.status)
        machine.details = node_request
        db.session.add(machine)
        db.session.commit()


@celery.task()
def delete_node(vm_name):
    driver = get_driver(Provider.RACKSPACE)
    conn = driver(
            app.config['USERNAME'],
            app.config['API_KEY'],
            region=app.config['AUTH_SYSTEM_REGION']
    )
    vm = Vm.query.filter_by(vm_name=vm_name, state='ACTIVE').first()
    found = False
    for node in conn.list_nodes():
        if node.name == vm.vm_name:
            node.destroy()
            vm.state = 'DELETED'
            vm.deleted_at = datetime.now()
            db.session.add(vm)
            db.session.commit()
            found = True
            break
    if found == False:
        logging.exception('Server not found')
