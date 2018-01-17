from flask_script import Server, Manager
from flask_migrate import  Migrate, MigrateCommand

from softserve import app, db

manager =  Manager(app)
manager.add_command('runserver', Server())
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
