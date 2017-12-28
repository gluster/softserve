from functools import wraps
from softserve import db, github
from model import *
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
            return jsonify({"response": "You must be the member of \
                                        gluster organization on Github to associate the bugs"}), 401
        return wrap
    return decorator

def sleep_time(hours):
    vm = db.session.query(Vm.created_at).filter


def delete_node(counts, cluster_name):
    for count in range(counts):
        node_name = str(count+1)+'.'+cluster_name
        node = nova.servers.find(node_name)
        node.delete()
        print('Deleting the node {}'.format(node_name))
        os.remove(cluster_name) #deleting the file containing the ips
