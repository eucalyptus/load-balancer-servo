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

import threading
import json

class ELBMetrics(object):
    '''
    http://docs.aws.amazon.com/ElasticLoadBalancing/latest/DeveloperGuide/US_MonitoringLoadBalancerWithCW.html
    '''
    def __init__(self, Latency=0, RequestCount=0, HTTPCode_ELB_4XX=0, HTTPCode_ELB_5XX=0, HTTPCode_Backend_2XX=0, HTTPCode_Backend_3XX=0, HTTPCode_Backend_4XX=0, HTTPCode_Backend_5XX=0):
        self.Latency=Latency
        self.RequestCount=RequestCount
        self.HTTPCode_ELB_4XX = HTTPCode_ELB_4XX
        self.HTTPCode_ELB_5XX = HTTPCode_ELB_5XX
        self.HTTPCode_Backend_2XX = HTTPCode_Backend_2XX
        self.HTTPCode_Backend_3XX = HTTPCode_Backend_3XX
        self.HTTPCode_Backend_4XX = HTTPCode_Backend_4XX
        self.HTTPCode_Backend_5XX = HTTPCode_Backend_5XX

    def __str__(self):
        return '%d-%d-%d-%d-%d-%d-%d-%d' % (self.Latency, self.RequestCount, self.HTTPCode_ELB_4XX, self.HTTPCode_ELB_5XX, self.HTTPCode_Backend_2XX, self.HTTPCode_Backend_3XX, self.HTTPCode_Backend_4XX, self.HTTPCode_Backend_5XX)

    def __repr__(self):
        return __str__(self)

class ProxyStatistics(object):
    def __init__(self):
        self.__num_request = 0
        self.__latency_sum = long(0)
        self.__http_elb_4xx = 0
        self.__http_elb_5xx = 0
        self.__http_be_2xx = 0
        self.__http_be_3xx = 0
        self.__http_be_4xx = 0
        self.__http_be_5xx = 0 
        self.cv =  threading.Condition()

    def received(self, log):
        self.cv.acquire()
        try:
            self.__num_request += log.get_request_count()
            self.__latency_sum += log.get_latency()
            status_code = log.get_status_code()
            if log.is_backend_code():
                if status_code >= 200 and status_code < 300:
                    self.__http_be_2xx += 1
                elif status_code >= 300 and status_code < 400:
                    self.__http_be_3xx += 1
                elif status_code >= 400 and status_code < 500:
                    self.__http_be_4xx += 1
                elif status_code >= 500 and status_code < 600:
                    self.__http_be_5xx += 1
            else:
                if status_code >= 400 and status_code <500:
                    self.__http_elb_4xx += 1
                elif status_code >=500 and status_code < 600:
                    self.__http_elb_5xx += 1
        finally:
            self.cv.release()

    def clear_all(self):
        self.__num_request = 0
        self.__latency_sum = long(0)
        self.__http_elb_4xx = 0
        self.__http_elb_5xx = 0
        self.__http_be_2xx = 0
        self.__http_be_3xx = 0
        self.__http_be_4xx = 0
        self.__http_be_5xx = 0 

    def get_json_and_clear_stat(self):
        self.cv.acquire()
        try:
            latency = long(self.__latency_sum)
            if self.__num_request <= 0:
                latency = 0
            elif latency < 0:
                latency = 0 
            m_map = {}
            m_map["Latency"] = str(latency)
            m_map["RequestCount"] = str(self.__num_request)
            m_map["HTTPCode_ELB_4XX"] = str(self.__http_elb_4xx)
            m_map["HTTPCode_ELB_5XX"] = str(self.__http_elb_5xx)
            m_map["HTTPCode_Backend_2XX"] = str(self.__http_be_2xx)
            m_map["HTTPCode_Backend_3XX"] = str(self.__http_be_3xx)
            m_map["HTTPCode_Backend_4XX"] = str(self.__http_be_4xx)
            m_map["HTTPCode_Backend_5XX"] = str(self.__http_be_5xx) 
            self.clear_all()
            return json.dumps(m_map)
        finally:
            self.cv.release()

stat_instance = ProxyStatistics()
