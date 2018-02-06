#!/usr/bin/env python
import datetime

from softserve import app, db
from softserve.model import User, Node_request, Vm
from softserve.lib import delete_node


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Node_request=Node_request, Vm=Vm)


@app.cli.command()
def shutdown_check():
    '''Command to shut down the VM when exceeding the time limit'''
    vms = Vm.query.filter_by(state='ACTIVE').all()
    if vms is None:
        pass
    else:
        for vm in vms:
            start_time = vm.created_at
            current_time = datetime.datetime.now()
            diff = current_time-start_time
            overall_seconds = diff.total_seconds()
            overall_hours = (overall_seconds) / 3600
            if overall_hours >= 4.0:
                name = vm.vm_name
                delete_node(name)
                vm.state = 'DELETED'
                db.session.commit()
            else:
                pass


if __name__ == '__main__':
    app.run()
