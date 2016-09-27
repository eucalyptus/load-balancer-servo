import boto
import xml.sax
import json
import os
import servo
from boto.resultset import ResultSet
from boto.compat import six
from servo.ws.loadbalancer import LoadBalancer

def unmarshall_lb(msg=None):   
    lbs = None
    try:
        markers = [('member', LoadBalancer)]
        rs = ResultSet(markers)
        h = boto.handler.XmlHandler(rs, None)
        if isinstance(msg, six.text_type):
            msg = msg.encode('utf-8')
        xml.sax.parseString(msg, h)
        lbs = rs
        for lb in lbs:
            print 'loadbalancer name: %s' % lb.name
    except Exception, err:
            print 'failed to parse loadbalancer message: %s' % str(err)

msg_file = '/tmp/loadbalancer'
if not os.path.exists(msg_file):
    raise Exception('no file exist in %s ' % msg_file)
else:
    f_msg = open(msg_file, 'r')
    msg = f_msg.read()
    f_msg.close()
    unmarshall_lb(msg)
