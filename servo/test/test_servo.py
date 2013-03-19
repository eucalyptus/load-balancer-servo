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

import os
import servo.ws
def describe(servo_id=None, host_name=None, aws_access_key_id=None, aws_secret_access_key=None):
    if aws_access_key_id is None:  
        aws_access_key_id=os.getenv('EC2_ACCESS_KEY')
    if aws_secret_access_key is None:
        aws_secret_access_key=os.getenv("EC2_SECRET_KEY")
    if host_name is None:
        import re
        r=re.compile('[\t\n\r://]+')
        host_name=r.split(os.getenv('EC2_URL'))[1]
 
    con = servo.ws.connect_elb(host_name=host_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    lb = con.get_servo_load_balancers(servo_id)
    print "loadbalancer: %s" % lb

