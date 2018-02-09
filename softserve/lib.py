'''
Shared library functions for softserve.
'''

import time
import re
import os
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
    flavor = nova.flavors.find(name='512MB Standard Instance')
    image = nova.images.find(name='CentOS 7 (PVHVM)')

    # create the nodes
    print(counts)
    public_key = open(os.path.expanduser("~/.ssh/id_rsa.pub")).read()
    keypair = nova.keypairs.create("mykeypair", public_key)
    for count in range(int(counts)):
        vm_name = str(count+1)+'.'+name
        node = nova.servers.create(name=vm_name, flavor=flavor.id,
                                   image=image.id, key_name=keypair.name)

        # wait for server to get active
        print(node.status)
        while node.status == 'BUILD':
            time.sleep(5)
            node = nova.servers.get(node.id)

        # get ip_address of the active node and store it in a file
        for network in node.networks['public']:
            if re.match(r'\d+\.\d+\.\d+\.\d+', network):
                machine = Vm(ip_address=network,
                             vm_name=vm_name,
                             state=node.status)
                machine.details = node_request
                db.session.add(machine)
                db.session.commit()
                # Storing the IP address of the machines in a file(filename is
                # same as that of the node name given by user) for future
                # purpose
                f = open(name, 'a')
                f.write("{}\n".format(network))
                f.close()


def delete_node(vm_name):
    node = nova.servers.find(name=vm_name)
    node.delete()
