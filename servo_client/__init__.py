import boto
from boto.ec2.elb import ELBConnection
from boto.ec2.regioninfo import RegionInfo

def connect_elb(host_name=None, port=8773, cluster=None, path="services/LoadBalancing", aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    region=RegionInfo(name=cluster, endpoint=host_name)
    
    return EucaServoConnection(region=region, port=port, path=path, aws_access_key_id=None, aws_secret_access_key=None, **kwargs)

class EucaServoConnection(ELBConnection):
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=False, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 security_token=None, validate_certs=True):
        """
        Init method to create a new connection to EC2 Load Balancing Service.

        note:: The region argument is overridden by the region specified in
            the boto configuration file.
        """
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        self.region = region

        ELBConnection.__init__(self, aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass, debug,
                                    https_connection_factory, region, path,
                                    security_token,
                                    validate_certs=validate_certs)

    def put_servo_states(self, servo_instance_id, instances):
        """
        Test the internal loadbalancer vms
        """
        params = {'InstanceId':servo_instance_id}
        if instances:
            self.build_list_params(params, instances, 'Instances.member.%d')
        return self.get_status('PutServoStates', params)

    def get_servo_load_balancers(self, servo_instance_id):
        marker = "servo:%s" % servo_instance_id
        params = {"Marker": marker}

        return self.get_list('DescribeLoadBalancers', params,
                             [('member', LoadBalancer)])
