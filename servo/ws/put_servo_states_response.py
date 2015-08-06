class PutServoStatesResult(object):
    def __init__(self, connection=None): 
        pass

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        pass

    def __repr__(self):
        return 'None'

class ResponseMetadata(object):
    def __init__(self, connection=None): 
        self.request_id = None 

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'RequestId':
            self.request_id = value

    def __repr__(self):
        return 'requestId: %s' % self.request_id
 
class ServoResponseMetadata(object):
    def __init__(self, connection=None): 
        self.get_lb_interval = None
        self.put_metric_interval = None
        self.put_instance_health_interval = None

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'GetLBInterval':
            self.get_lb_interval = int(value)
        elif name == 'PutMetricInterval':
            self.put_metric_interval = int(value)
        elif name == 'PutInstanceHealthInterval':
            self.put_instance_health_interval = int(value)

    def __repr__(self):
        return 'getLbInterval: %d, putMetricInterval: %d, putInstanceHealthInterval: %d' % (self.get_lb_interval, self.put_metric_interval, self.put_instance_health_interval)

class PutServoStatesResponseType(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.put_servo_states_result = None 
        self.response_metadata = None
        self.servo_response_metadata = None

    def startElement(self, name, attrs, connection):
        if name == 'PutServoStatesResult':
            self.put_servo_states_result = PutServoStatesResult(connection)
            return self.put_servo_states_result
        elif name == 'ResponseMetadata':
            self.response_metadata = ResponseMetadata(connection)
            return self.response_metadata
        elif name == 'ServoResponseMetadata':
            self.servo_response_metadata = ServoResponseMetadata(connection)
            return self.servo_response_metadata
        else:
            return None

    def endElement(self, name, value, connection):
        pass

    def __repr__(self):
        return 'PutServoStatesResponse (%s,%s,%s)' % ( repr(self.put_servo_states_result), repr(self.response_metadata), repr(self.servo_response_metadata))
