import redis
import time
import boto
import xml.sax
from boto.resultset import ResultSet
from boto.compat import six
from servo.ws.loadbalancer import LoadBalancer

def set_load_balancer(msg):
    if not 'data' in msg or not msg['data']:
        return
    msg = msg['data']
    print 'message: %s ' % msg
    markers = [('member', LoadBalancer)]
    rs = ResultSet(markers)
    h = boto.handler.XmlHandler(rs, None)
    if isinstance(msg, six.text_type):
        msg = msg.encode('utf-8')
    xml.sax.parseString(msg, h)
    lbs = rs
    for lb in lbs:
        print 'elb: %s, listeners: %d' % (lb.name, len(lb.listeners))

r = redis.StrictRedis(host='localhost', port=6379)
p = r.pubsub()
p.subscribe(**{'set-loadbalancer': set_load_balancer})

for msg in p.listen():
    pass


