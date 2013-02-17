# Copyright 2009-2013 Eucalyptus Systems, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
# Please contact Eucalyptus Systems, Inc., 6755 Hollister Ave., Goleta
# CA 93117, USA or visit http://www.eucalyptus.com/licenses/ if you need
# additional information or have any questions.

from util import TimeoutError
from listener import Listener
import os
import shutil
import servo
import config
import traceback
import sys
from haproxy_conf import ConfBuilderHaproxy
from haproxy_process import HaproxyProcess

CONF_FILE = config.RUN_ROOT+"/euca_haproxy.conf"
CONF_FILE_TEMPLATE = config.INSTALL_ROOT+"/haproxy_template.conf"
PID_PATH = config.RUN_ROOT+"/haproxy.pid"

class ProxyActionTransaction(object):
    def __init__(self, actions=[]):
        self._actions = actions

    @staticmethod
    def getInstance(actions=[]):
        return ProxyActionDefaultTransaction(actions)

    # queue and run periodcally? or run immediately?
    def run(self):
        raise NotImplementedError 

class ProxyActionDefaultTransaction(ProxyActionTransaction):
     def __init__(self, actions):
         ProxyActionTransaction.__init__(self, actions)
         
     def run(self):
         if not os.path.exists(CONF_FILE):
             if os.path.exists(CONF_FILE_TEMPLATE): 
                 shutil.copy2(CONF_FILE_TEMPLATE, CONF_FILE)
             else:
                 raise ProxyError("cannot find the haproxy template file")
         # retain the existing config
         conf_backup = '%s.backup' % CONF_FILE 
         shutil.copy2(CONF_FILE, conf_backup)

         # update config files by ProxyAction
         for action in self._actions:
             try:
                 servo.log.debug(action)
                 action.run()  # will replace the haconfig file in-place
             except Exception, err: 
                 servo.log.error('update failed: %s' % err)
                 servo.log.warning('failed to run the action. reverting the change')
                 #copy the backup back to the original
                 shutil.copy2(conf_backup, CONF_FILE)
                 os.unlink(conf_backup)
                 return False

         # kill and restart the haproxy process
         try:
             proc = HaproxyProcess(conf_file = CONF_FILE, pid_path=PID_PATH)
             if proc.getStatus() == HaproxyProcess.TERMINATED:
                 proc.run() 
                 servo.log.debug("new haproxy process started")
             else:
                 proc.restart()
                 servo.log.debug("haproxy process restarted")
         except Exception, err:
             # if not, replace back to old config, restart the haproxy process (if still fails, that's bad!) 
             try:
                 if proc is not None:
                     proc.terminate()
             except:
                 pass
             traceback.print_exc(file=sys.stdout)
             servo.log.error('failed to run haproxy process: %s' % err)
             servo.log.debug('old haproxy config is in %s' % conf_backup)
             return False
        
         os.unlink(conf_backup)
         return True

class ProxyAction(object):
    STATUS_PENDING = 0
    STATUS_DONE = 1
    STATUS_ERROR = 2
    def __init__(self):
        pass

    def run(self):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError

class ProxyCreate(ProxyAction):
    def __init__(self, listener):
        if not isinstance(listener, Listener):
            raise TypeError 
        self.__listener = listener
        self.__status = ProxyAction.STATUS_PENDING 
    
    def run(self):
        # HaproxyConfBuilder 
        # from the current haproxy config
        # update config
        # replace the config
        
        #def add(self, protocol, port, instances=[]):
        #instance = {hostname , port, protocol=None )
        builder = ConfBuilderHaproxy(CONF_FILE) 
        instances = []

        for host in self.__listener.getInstances():
            instance = {'hostname':host, 'port': self.__listener.getInstancePort(), 'protocol': self.__listener.getInstanceProtocol()}
            instances.append(instance)
        try: 
            builder.add(protocol=self.__listener.getProtocol(), port=self.__listener.getPort(), instances=instances).build(CONF_FILE)
        except Exception, err:
            self.__status =ProxyAction.STATUS_ERROR
            servo.log.error('failed to add new frontend to the config: %s' % err)
            return
        self.__status = ProxyAction.STATUS_DONE

    def status(self):
        return self.__status

    def __repr__(self):
        return "ProxyCreate action (update haproxy config file)"

    def __str__(self):
        return self.__repr__()

class ProxyRemove(ProxyAction):
    def __init__(self, listener):
        if not isinstance(listener, Listener):
            raise TypeError 
        self.__listener = listener
        self.__status = ProxyAction.STATUS_PENDING 
    def run(self):
        builder = ConfBuilderHaproxy(CONF_FILE)
        portToRemove = self.__listener.getPort()
        try: 
            builder.removeProtocolPort(portToRemove).build(CONF_FILE)
        except Exception, err:
            servo.log.error("failed to remove the port from the haproxy config: %s" % err)
            self.__status =ProxyAction.STATUS_ERROR
            return
        self.__status = ProxyAction.STATUS_DONE

    def __repr__(self):
        return "ProxyRemove action (update haproxy config file)"

    def __str__(self):
        return self.__repr__()

    def status(self):
        return self.__status

class ProxyAddInstance(ProxyAction):
    def __init__(self, instance):
        self.instance = instance
    
    def run(self):
        pass 
    
    def status(self):
        pass

class ProxyRemoveInstance(ProxyAction):
    def __init__(self, instance):
        self.instace = instance

    def run(self):
        pass

    def status(self):
        pass

class ProxyInterface(object):
    """
    Represent the commands that underlying proxy will perform
    """ 
    def create(self, listener):
        raise NotImplementedError 

    def update(self, listener):
        raise NotImplementedError

    def teardown(self, listener):
        raise NotImplementedError

    def addBackend(self, instance):
        raise NotImplementedError
   
    def removeBackend(self, instance):
        raise NotImplementedError
