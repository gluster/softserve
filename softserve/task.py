from model import Vm
from lib import delete_node, service_provider_config
from softserve import db

@service_provider_config
def shutdown_check():
        #vm = Vm.query.filter_by(Vm.user.id == g.user.id, Vm.state == 'ACTIVE')
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
