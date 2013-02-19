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

RUN_ROOT = "/var/run/eucaservo"
LOG_FILE = "/var/log/eucaservo.log"
INSTALL_ROOT = "/root"# os.environ['SERVO_HOME']
QUERY_PERIOD_SEC = 10

def get_access_key_id():
    return 'XZI553LGSDQFGEOLKQ0CH'  # TODO: IAM role

def get_secret_access_key():
    return 'Awqmvo2XL3KWfEmbN4MI2l8zr0I76b5Cq85jZrbx' #TODO: IAM role

def get_clc_host():
    return '192.168.0.108' #TODO

def get_clc_port():
    return 8773 #TODO

def get_ec2_path():
    return 'services/Eucalyptus' #TODO

def get_availability_zone():
    return 'PARTI00' #TODO
