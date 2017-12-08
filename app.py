#!/usr/bin/env python

from flask import Flask, request, render_template,
import argparse
import os
import sys
import time
import re
import pyrax
#from libcloud.compute.types import Provider
#from libcloud.compute.providers import get_driver
#from libcloud.compute.base.NodeDriver import import_key_pair_from_file

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/create_node', methods=['POST'])
def getdata():
    pyrax.set_setting('identity_type', os.environ['OS_AUTH_SYSTEM'])
    pyrax.set_default_region(os.environ['OS_REGION_NAME'])
    pyrax.set_credentials(os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'])
    nova = pyrax.cloudservers

    #get the SSH key
    counts = request.form['counts']
    cluster_name = request.form['cluster_name']
    hours = request.form['hours']

    flavor = nova.flavors.find(name='512MB Standard Instance')
    image = nova.images.find(name='Ubuntu 14.04 LTS (Trusty Tahr)')
    key_name = #name of SSH public key

    # create the nodes
    for count in range(counts):
        node_name = str(count+1)+'.'+cluster_name
        node = nova.servers.create(name=node_name, flavor=flavor.id, image=image.id, key_name=key_name)

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







if __name__=="__main__":
    app.run(debug=True)
