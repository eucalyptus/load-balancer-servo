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

import logging
import logging.config
import config
from proxy import ProxyActionTransaction
from proxy import ProxyCreate
from proxy import ProxyRemove
from util import ServoError
from listener import Listener

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

format_string = "%(asctime)s %(name)s [%(levelname)s]:%(message)s"
logging.basicConfig(filename=config.LOG_FILE, level=logging.DEBUG, format=format_string)
log = logging.getLogger('servo')
console = logging.StreamHandler()
log.addHandler(console)

'''
    Keep the state of listeners; 
    Receive the new specification;
    Trigger actions if necesary;
    Describe current actions;
    Configure health check; 
'''
class ProxyManager(object):
    def __init__(self):
        self.__listeners = [] # existing listeners
        pass

    def updateListeners(self, listeners=[]):
        to_add = []
        to_delete = [] 
        # find any listener that's updated
        for exist in self.__listeners:
            if not exist in listeners:
                to_delete.append(exist) 

        # find any new listener
        for incoming in listeners:
            if not incoming in self.__listeners:
                to_add.append(incoming)
        log.debug("to-add: %d, to-delete: %d" % (len(to_add), len(to_delete)))
        if len(to_delete) == 0 and len(to_add) == 0:
            return self.__listeners

        proxy_actions = [] 
        for delete in to_delete:
            proxy_actions.append(ProxyRemove(delete))
        for add in to_add:
            proxy_actions.append(ProxyCreate(add))
        try:
            ok = ProxyActionTransaction.getInstance(proxy_actions).run() 
        except Exception, error:
            log.error('failed to update the listeners (%s)' % error)
            return self.__listeners

        # update listeners
        if ok:
            for deleted in to_delete:
                self.__listeners.remove(deleted)
            for added in to_add:
                self.__listeners.append(added)

        return self.__listeners

    def getListeners(self):
         return self.__listeners
