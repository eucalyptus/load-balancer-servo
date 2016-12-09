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
* HAProxy >= 1.5-dev17
* python-boto >= 2.8.0
* python-httplib2
* sudo

Installing from the repository
------------------------------

To install the *load-balancer-servo* package straight from the repository, run:

    $ ./install-servo.sh

This will create various directories and copy configuration files, as well as
create a *servo* user account.

Starting the service
--------------------

The *load-balancer-servo* service can be started by running:

    $ systemctl start load-balancer-servo

Please Note: This service will **not** work unless it is running on a Eucalyptus
instance that has been instantiated by the Eucalyptus LoadBalancer service.

