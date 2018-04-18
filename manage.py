#!/usr/bin/env python
import datetime
import click

from softserve import app, db
from softserve.model import User, NodeRequest, Vm
from softserve.lib import delete_node


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, NodeRequest=NodeRequest, Vm=Vm)


@app.cli.command()
def shutdown_check():
    '''Command to shut down the VM when exceeding the time limit'''
    vms = Vm.query.filter_by(state='ACTIVE').all()
    if vms == []:
        pass
    else:
        for vm in vms:
            start_time = vm.created_at
            current_time = datetime.datetime.now()
            diff = current_time-start_time
            overall_seconds = diff.total_seconds()
            overall_hours = (overall_seconds) / 3600
            node = NodeRequest.query.filter(vm.details_id == NodeRequest.id) \
                .join(Vm).first()
            if overall_hours >= node.hours:
                delete_node.delay(vm.vm_name)
            else:
                pass


@app.cli.command()
@click.option('--username', default=None, help='github username to add')
def make_admin(username):
    '''Command to make a user as an admin of softserve'''
    app.config['ADMINS'].append(username)
    user = User.query.filter(username == username).first()
    user.admin = True
    db.session.add(user)
    db.session.commit()


if __name__ == '__main__':
    app.run()
