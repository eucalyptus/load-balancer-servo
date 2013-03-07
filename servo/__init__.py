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
from servo.config import LOG_FILE, set_pidfile
from servo.main_loop import ServoLoop

__version__ = '1.0.0-dev'
Version = __version__

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

format_string = "%(asctime)s %(name)s [%(levelname)s]:%(message)s"
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format=format_string)
log = logging.getLogger('servo')
console = logging.StreamHandler()
log.addHandler(console)

def start_servo():
    # TODO: should daemonize 
    ServoLoop().start()
