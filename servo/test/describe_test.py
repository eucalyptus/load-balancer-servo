#
import servo.ws
con = servo.ws.connect_elb(host_name='192.168.0.108', aws_access_key_id='XZI553LGSDQFGEOLKQ0CH', aws_secret_access_key='Awqmvo2XL3KWfEmbN4MI2l8zr0I76b5Cq85jZrbx')
lb = con.get_servo_load_balancers('i-4215418F')
print "loadbalancer: %s" % lb

