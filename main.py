#!/usr/bin/env python
import os
import sys
import time
import re
import pyrax
import github3 import login
import requests
import sys

def login(username, password):
    gh = login('{}', password='{}'.format(username, password))

def check_membership(username):
    d = requests.get('https://api.github.com/orgs/gluster/members?per_page=200') #get the list of public members
    data = d.json()
    members = [str(details["login"]) for details in data]
    if username not in members:
        print("Not a public member of Gluster.org") #checking for public members
        sys.exit(1)

def get_publicSSHkey():
    #Upload the public key through form

def create_node(key_name, counts, cluster_name):
    flavor = nova.flavors.find(name=' ') #2048MB
    image = nova.images.find(name=' ') #CentOS 7
    #key_name = #name of the SSSH public key_name

    for count in range(counts):
        node_name = str(count+1)+'.'+cluster_name
        node = nova.servers.create(name=node_name, flavor=flavor.id, image=image.id, key_name=key_name)
        print('Creating the node {}'.format(node_name))
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

def delete_node(counts, cluster_name):
    for count in range(counts):
        node_name = str(count+1)+'.'+cluster_name
        node = nova.servers.find(node_name)
        node.delete()
        print('Deleting the node {}'.format(node_name))
        os.remove(cluster_name) #deleting the file containing the ips


def main():
    global nova
    pyrax.set_setting('identity_type', os.environ['OS_AUTH_SYSTEM'])
    pyrax.set_default_region(os.environ['OS_REGION_NAME'])
    pyrax.set_credentials(os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'])
    nova = pyrax.cloudservers

    check_membership(username='deepshikhaaa')

    create_node(key_name='id_rsa.pub', counts=2, cluster_name='test')

    time.sleep(21600)  #for 6 hours, will take this input in app.py code from user

    delete_node(counts=2, cluster_name='test')
