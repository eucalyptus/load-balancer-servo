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
if __name__ == "__main__":
    from servo import ProxyManager, Listener

    print "TEST -- CREATE NEW LISTENER"  
    first = Listener(protocol='tcp', port=80, instance_port=80)
    first.addInstance('192.168.0.100')
    proxy = ProxyManager() 
    proxy.updateListeners([first])
    current = proxy.getListeners()
    if len(current) == 1 and first in current:
        print "PASSED: new listener added"
    else:
        print "ERROR: new listener not found"

    print "TEST -- ADD NEW LISTENER"
    second = Listener(protocol='http', port=82, instance_port=80)
    second.addInstance('192.168.0.101')
    second.addInstance('192.168.0.102')
    proxy.updateListeners([first, second])
    current = proxy.getListeners()
    if len(current) ==2 and first in current and second in current:
        print "PASSED: second listener added"
    else:
        print "ERROR: second listener not added"

    print "TEST -- KEEP SAME LISTENERS"
    second_copy = Listener(protocol='http', port=82, instance_port=80)
    second_copy.addInstance('192.168.0.101')
    second_copy.addInstance('192.168.0.102')
    proxy.updateListeners([first, second_copy])
    current = proxy.getListeners()
    if len(current) ==2 and first in current and second in current:
        print "PASSED: second listener still in the list" 
    else:
        print "ERROR: second listener not added"

    print "TEST -- REMOVE LISTENER"
    proxy.updateListeners([first])
    current = proxy.getListeners()
    if len(current) ==1 and first in current:
        print "PASSED: second listener removed"
    else:
        print "ERROR: second listener not removed"
   
    print "TEST -- ADD MULTIPLE NEW LISTENER"
    third = Listener(protocol='http', port=83, instance_port=82)
    fourth = Listener(protocol='http', port=84, instance_port=83)
    proxy.updateListeners([first, third, fourth])
    current = proxy.getListeners()
    if len(current) == 3 and first in current and third in current and fourth in current:
        print "PASSED: third, fourth listener added"
    else:
        print "ERROR: third listener not added"

    print "TEST -- MODIFY INSTANCE MEMBERSHIP"
    new_fourth = Listener(protocol='http', port=84, instance_port=83)
    new_fourth.addInstance('192.168.0.109')
    proxy.updateListeners([first,third,new_fourth])
    current = proxy.getListeners()
    if len(current) == 3 and first in current and third in current and new_fourth in current:
        print "PASSED: new instance added"
    else:
        print "ERROR: third listener not added"
