load-balancer-servo
===================

What is this?
-------------

The *load-balancer-servo* is a service that is installed in the Eucalyptus
Load Balancer EMI. It works in conjunction with HAProxy and proxies commands
and configuration settings to it.

Prerequisites
-------------

In order to use *load-balancer-servo*, you will need a few things:

* A Eucalyptus EMI on which to install the service
* HAProxy 1.5-dev17 or newer installed in the EMI
* python-boto
* python-httplib2

Installing from the repository
------------------------------

To install the *load-balancer-servo* package straight from the repository, run:

    $ ./install-servo.sh

This will create various directories and copy configuration files, as well as
create a *servo* user account.

Starting the service
--------------------

The *load-balancer-servo* service can be started by running:

    $ service load-balancer-servo start

Please Note: This service will **not** work unless it is running on a Eucalyptus
instance that has been instantiated by the Eucalyptus Balancer service.

