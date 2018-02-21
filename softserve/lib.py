'''
Shared library functions for softserve.
'''

import time
import re
from sshpubkeys import SSHKey
from functools import wraps
from flask import jsonify
from softserve import db, github, nova
from softserve.model import Vm


def organization_access_required(org):
    """
    Decorator that can be used to validate the presence of user in a particular
    organization.
    """
    def decorator(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            orgs = github.get('user/orgs')
            print(orgs)
            for org_ in orgs:
                if org_['login'] == org:
                    return func(*args, **kwargs)
            return jsonify({"response": "You must be the member of gluster \
                                         organization on Github to serve \
                                         yourself machines \
                                         for testing"}), 401
        return wrap
    return decorator


def create_node(counts, name, node_request, pubkey):
    '''
    Create a node in the cloud provider
    '''
    flavor = nova.flavors.find(name='1 GB General Purpose v1')
    image = nova.images.find(name='CentOS 7 (PVHVM)')

    # create the nodes

    '''Validating the SSH public key'''
    ssh = SSHKey(pubkey, strict=True)
    try:
        ssh.parse()
    except:
        raise Exception("Unable to validate SSH")
    keypair = nova.keypairs.create(name, pubkey)
    for count in range(int(counts)):
        vm_name = 'softserve-'+name+'.'+str(count+1)
        node = nova.servers.create(name=vm_name, flavor=flavor.id,
                                   image=image.id, key_name=keypair.name)

        # wait for server to get active
        print(node.status)
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


def delete_node(vm_name):
    node = nova.servers.find(name=vm_name)
    node.delete()
