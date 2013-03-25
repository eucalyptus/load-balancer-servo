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

class HaproxyLog(object):
    def get_latency(self):  # in milliseconds
        raise NotImplementedError()

    def get_request_count(self):
        raise NotImplementedError()

    def get_status_code(self):
        raise NotImplementedError()

    def is_backend_code(self):
        raise NotImplementedError()
     

class HttpLog(HaproxyLog):
    def __init__(self, frontend_name=None, backend_name=None, server_name=None, status_code=200, term_state='--', Tq=0, Tw=0, Tc=0, Tr=0, Tt=0):
        self.frontend_name = frontend_name
        self.backend_name = backend_name
        self.server_name = server_name
        self.status_code = status_code
        self.term_state = term_state
        self.Tq = Tq  #the total time in milliseconds spent waiting for the client to send a full HTTP request
        self.Tw = Tw  #total time in milliseconds spent waiting in the various queues.
        self.Tc = Tc  #total time in milliseconds spent waiting for the connection to establish to the final server, including retries
        self.Tr = Tr  #total time in milliseconds spent waiting for the server to send a full HTTP response
        self.Tt = Tt  # total time in milliseconds elapsed between the accept and the last close 

    def get_latency(self):
        return self.Tt

    def get_request_count(self):
        return 1
 
    def get_status_code(self):
        return int(self.status_code)

    def is_backend_code(self):
        # TODO: SPARK: more sophisticated logic to classify the termination state would be needed
        # any session who's termination state is not '--' represents that the haproxy detected error with the session and 
        # sent the http status code accordingly to the client
        if self.term_state == '--': 
            return True
        else:
            return False 

    @staticmethod
    def parse(line):
        # self.__content_map[section_name].append('logformat httplog\ %f\ %b\ %s\ %ST\ %ts\ %Tq\ %Tw\ %Tc\ %Tr\ %Tt') 
        token = line.split(' ')
        if len(token) == 11:
            log = HttpLog()
            log.frontend_name = token[1]
            log.backend_name = token[2]
            log.server_name = token[3]
            log.status_code = int(token[4])
            log.term_state = token[5]
            log.Tq = int(token[6])
            log.Tw = int(token[7])
            log.Tc = int(token[8])
            log.Tr = int(token[9])
            log.Tt = int(token[10])
            return log
        raise Exception()
 
    def __str__(self):
        return 'httplog-%s-%s-%s-%d-%s-%d-%d-%d-%d-%d' % (self.frontend_name, self.backend_name, self.server_name, self.status_code, self.term_state, self.Tq, self.Tw, self.Tc, self.Tr, self.Tt)

    def __repr__(self):
        return __str__(self)

class TcpLog(HaproxyLog):
    def __init__(self, frontend_name=None, backend_name=None, server_name=None, term_state='--', Tw=0, Tc=0, Tt=0):
        self.frontend_name = frontend_name
        self.backend_name = backend_name
        self.server_name = server_name
        self.term_state = term_state
        self.Tw = Tw  #total time in milliseconds spent waiting in the various queues.
        self.Tc = Tc  #total time in milliseconds spent waiting for the connection to establish to the final server, including retries
        self.Tt = Tt  # total time in milliseconds elapsed between the accept and the last close 

    def get_latency(self):  # in milliseconds
        return self.Tt

    def get_request_count(self):
        return 1

    def get_status_code(self):
        return 0 # irrelevant

    def is_backend_code(self):
        return True #irrelevant

    @staticmethod
    def parse(line):
        # self.__content_map[section_name].append('log-format tcplog\ %f\ %b\ %s\ %ts\ %Tw\ %Tc\ %Tt') 
        token = line.split(' ')
        if len(token) == 8:
            log = TcpLog()
            log.frontend_name = token[1]
            log.backend_name = token[2]
            log.server_name = token[3]
            log.term_state = token[4]
            log.Tw = int(token[5])
            log.Tc = int(token[6])
            log.Tt = int(token[7])
            return log
        raise Exception()
 
    def __str__(self):
        return 'tcplog-%s-%s-%s-%s-%d-%d-%d' % (self.frontend_name, self.backend_name, self.server_name, self.term_state, self.Tw, self.Tc, self.Tt)

    def __repr__(self):
        return __str__(self)
