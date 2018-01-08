# Softserve
Web application for self serving fixed duration VMs to carry out debugging in Gluster project. The served VMs will get automatically removed after a fixed number of hours (4 hrs, can be changed lately).

## Installation
* Before you start installation make sure you have a working installation of python2
* Create and activate virtualenv
* In your virtualenv run ```pip install -r requirements.txt```
* Now you are all ready with the installation

## Description
* Launch the VMs as per the need of the user.
* Tear down automatically after a specific number of hours. This is a requirement so that the machine time is used judicially and tied down to a specific bug
* Allow users who are in the Gluster organization on Github to request VMs.
* Users should be able to upload their SSH public key and they will get access to the machines when it is created.

## Usage
* Run migrations and setup database `python manage.py db upgrade`
* To run the softserve app on localhost run `python manage.py runserver`
* Create application.cfg and add `DEBUG=True` to it to enable debug mode for your flask app
* By default fstat reads and writes the data into sqlite but it can be overriden in your application.cfg

## TODO
* Add the deleting functionality in the code
* Write the test cases
