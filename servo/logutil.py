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
from logging.handlers import RotatingFileHandler

#
# We can't specify the log file in the config module since that will
# import boto and keep us from initializing the boto logger.
#
LOG_FILE = '/var/log/load-balancer-servo/servo.log'
LOG_BYTES = 1024 * 1024 # 1MB
LOG_FORMAT = "%(asctime)s %(name)s [%(levelname)s]:%(message)s"
LOG_HANDLER = RotatingFileHandler(LOG_FILE, maxBytes=LOG_BYTES, backupCount=5)


logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT)
log = logging.getLogger('servo')
botolog = logging.getLogger('boto')
log.setLevel(logging.INFO)
botolog.setLevel(logging.INFO)
log.addHandler(LOG_HANDLER)
botolog.addHandler(LOG_HANDLER)


# Log level will default to WARN
# If you want more information (like DEBUG) you will have to set the log level
def set_loglevel(lvl):
    global log
    log.setLevel(get_log_level_as_num(lvl))


def set_boto_loglevel(lvl):
    botolog.setLevel(get_log_level_as_num(lvl))


def get_log_level_as_num(lvl):
    lvl_num = None
    if isinstance(lvl, str):
        try:
            lvl_num = logging.__getattribute__(lvl.upper())
        except AttributeError:
            log.warn("Failed to set log level to '%s'" % lvl)
            return
    else:
        lvl_num = lvl
    return lvl_num
