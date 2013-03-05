#
import servo.ws
con = servo.ws.connect_elb(host_name='10.111.1.67', aws_access_key_id='5OKTUB0YQPL1KLIGUCWXX', aws_secret_access_key='JTYZHygfWzIpu4Kaz3LaEZ3JCVaQ8NjNNXQtGxCI')
lb = con.get_servo_load_balancers('i-4215418F')
print "loadbalancer: %s" % lb

