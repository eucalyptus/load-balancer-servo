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
from servo.haproxy import ProxyManager, Listener
mytest=1
if __name__ == "__main__":
    print "TEST -- CREATE NEW LISTENER"  
    first = Listener(protocol='tcp', port=80, instance_port=80, loadbalancer='lb01')
    first.add_instance('192.168.0.100')
    proxy = ProxyManager() 
    proxy.update_listeners([first])
    current = proxy.listeners()
    if len(current) == 1 and first in current:
        print "PASSED: new listener added"
    else:
        print "ERROR: new listener not found"

    print "TEST -- ADD NEW LISTENER"
    second = Listener(protocol='http', port=82, instance_port=80, loadbalancer='lb02')
    second.add_instance('192.168.0.101')
    second.add_instance('192.168.0.102')
    proxy.update_listeners([first, second])
    current = proxy.listeners()
    if len(current) ==2 and first in current and second in current:
        print "PASSED: second listener added"
    else:
        print "ERROR: second listener not added"

    print "TEST -- KEEP SAME LISTENERS"
    second_copy = Listener(protocol='http', port=82, instance_port=80, loadbalancer='lb02')
    second_copy.add_instance('192.168.0.101')
    second_copy.add_instance('192.168.0.102')
    proxy.update_listeners([first, second_copy])
    current = proxy.listeners()
    if len(current) ==2 and first in current and second in current:
        print "PASSED: second listener still in the list" 
    else:
        print "ERROR: second listener not added"

    print "TEST -- REMOVE LISTENER"
    proxy.update_listeners([first])
    current = proxy.listeners()
    if len(current) ==1 and first in current:
        print "PASSED: second listener removed"
    else:
        print "ERROR: second listener not removed"
   
    print "TEST -- ADD MULTIPLE NEW LISTENER"
    third = Listener(protocol='http', port=83, instance_port=82, loadbalancer='lb03')
    fourth = Listener(protocol='http', port=84, instance_port=83, loadbalancer='lb04')
    proxy.update_listeners([first, third, fourth])
    current = proxy.listeners()
    if len(current) == 3 and first in current and third in current and fourth in current:
        print "PASSED: third, fourth listener added"
    else:
        print "ERROR: third listener not added"

    print "TEST -- MODIFY INSTANCE MEMBERSHIP"
    new_fourth = Listener(protocol='http', port=84, instance_port=83, loadbalancer='lb04')
    new_fourth.add_instance('192.168.0.109')
    proxy.update_listeners([first,third,new_fourth])
    current = proxy.listeners()
    if len(current) == 3 and first in current and third in current and new_fourth in current:
        print "PASSED: new instance added"
    else:
        print "ERROR: third listener not added"
