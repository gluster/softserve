'''
Shared library functions for softserve.
'''
import logging
import socket
from datetime import datetime
from functools import wraps
import time
import boto.ec2

from flask import jsonify, g, redirect, url_for, request
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.base import NodeAuthSSHKey
from libcloud.compute.deployment import SSHKeyDeployment, MultiStepDeployment

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
    conn = boto.ec2.connect_to_region(app.config['REGION_NAME'])
    key = conn.import_key_pair(name, pubkey)
    for count in range(int(counts)):
        vm_name = ''.join(['softserve-', name, '.', str(count+1)])

        reservation = conn.run_instances(
                      'ami-04f22a6831d585e63',
                      key_name=name,
                      instance_type='t3.small',
                      security_groups=['regression'])

        instance = reservation.instances[0]

        # wait for instance to be running
        while instance.update() != "running":
            time.sleep(5)

        # add instance tag
        instance.add_tag("Name",vm_name)

        state = str(instance.state)
        ip_address = instance.ip_address

        node_request = NodeRequest.query.filter_by(id=node_request).first()

        machine = Vm(ip_address=ip_address,
                     vm_name=vm_name,
                     state=state)
        machine.details = node_request
        db.session.add(machine)
        db.session.commit()

    #delete imported key pair after creation
    conn.delete_key_pair(name)


@celery.task()
def delete_node(vm_name):
    conn = boto.ec2.connect_to_region(app.config['REGION_NAME'])
    # get the list of running instances on AWS
    reservations=conn.get_all_reservations(filters={'instance-state-name': 'running'})
    machine = Vm.query.filter_by(vm_name=vm_name, state='running').first()
    found = False
    for reservation in reservations:
        for node in reservation.instances:
            if str(node.tags['Name']) == machine.vm_name:
                node.terminate()
                machine.state = 'deleted'
                machine.deleted_at = datetime.now()
                db.session.add(machine)
                db.session.commit()
                found = True
                break
    if found is False:
        logging.exception('Server not found')
