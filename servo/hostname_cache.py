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

import boto
import config
from boto.ec2.regioninfo import RegionInfo

__hostname_map = {}
def get_hostname(instance_id):
    if instance_id in __hostname_map:
        return  __hostname_map[instance_id]
    else:
        region = RegionInfo(name=config.get_availability_zone(), endpoint=config.get_clc_host())
        conn=boto.connect_ec2(region=region, aws_access_key_id=config.get_access_key_id(), aws_secret_access_key=config.get_secret_access_key(), port=config.get_clc_port(), path=config.get_ec2_path(), is_secure=False)
        resvs = conn.get_all_instances(instance_ids=[instance_id])
        if resvs is not None and len(resvs)>0:
            for resv in resvs:
                for instance in resv.instances:
                    if instance.id == instance_id:
                        __hostname_map[instance_id] = str(instance.private_ip_address)  #TODO: right to assume private ip is always available and reachable from lb vms? (security group?)
                        return __hostname_map[instance_id]
        

