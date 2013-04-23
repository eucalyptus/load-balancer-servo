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

import string
import logging
import logging.config

from servo.config import LOG_FILE

_format_string = "%(asctime)s %(name)s [%(levelname)s]:%(message)s"
logging.basicConfig(filename=LOG_FILE, level=logging.WARN, format=format_string)
log = logging.getLogger('servo')
_console = logging.StreamHandler()
log.addHandler(_console)

# Log level will default to WARN
# If you want more information (like DEBUG) you will have to set the log level
def set_loglevel(lvl):
    global log
    lvl_num = None
    if isinstance(lvl, str):
        try:
            lvl_num = logging.__getattribute__(string.upper(lvl))
        except AttributeError:
            log.warn("Failed to set log level to '%s'" % lvl)
            return
    else:
        lvl_num = lvl

    log.setLevel(lvl_num)

