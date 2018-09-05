'''
Shared library functions for softserve.
'''
import logging
import socket
from datetime import datetime
from functools import wraps

from flask import jsonify, g, redirect, url_for, request
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.deployment import SSHKeyDeployment

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
            return jsonify({
                "response": "You must be the member of gluster"
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

    # Terrible hack to workaround libcloud bug #1011
    # On python 3 a unicode string should be str. On python2, we will have to
    # force unicode to str. Otherwise libcloud doesn't recognize it.
    if not isinstance(pubkey, str):
        str(pubkey)

    step = SSHKeyDeployment(pubkey)
    node_request = NodeRequest.query.get(node_request)
    for count in range(int(counts)):
        vm_name = ''.join(['softserve-', name, '.', str(count+1)])
        node = conn.deploy_node(
            name=vm_name, image=image, size=flavor, deploy=step
        )
        for ip_addr in node.public_ips:
            try:
                socket.inet_pton(socket.AF_INET, ip_addr)
                network = ip_addr
            except socket.error:
                continue
        machine = Vm(ip_address=network,
                     vm_name=vm_name,
                     state=node.state)
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
    machine = Vm.query.filter_by(vm_name=vm_name, state='running').first()
    found = False
    for node in conn.list_nodes():
        if node.name == machine.vm_name:
            node.destroy()
            machine.state = 'DELETED'
            machine.deleted_at = datetime.now()
            db.session.add(machine)
            db.session.commit()
            found = True
            break
    if found is False:
        logging.exception('Server not found')
