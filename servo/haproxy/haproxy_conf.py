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

import os
import base64
import servo
import servo.config as config
class ConfBuilder(object):
    def __init__(self, source):
        ## read the file contents
        self.contents = []
        try:
            f=open(source, "r")
            self.contents = f.readlines()
            f.close()
        except Exception, err:
            servo.log.error('failed to open file %s' % source)
 
    def build(self, destination=None):
        raise NotImplementedException

    def add(self, protocol, port, instances=[], cookie_name=None, cookie_expire=None, cert=None, comment=None):
        try:
            self.add_protocol_port(protocol, port, cookie_name, cookie_expire, cert, comment )
            for instance in instances:
                self.add_backend(port, instance)
        except Exception, err:
            servo.log.error('failed to add protocol-port: %s' % err)
        return self

    def add_protocol_port(self, protocol, port, cookie_name=None, cookie_expire=None, cert=None, comment=None):
        raise NotImplementedError
  
    def remove_protocol_port(self, port):
        raise NotImplementedError

    def add_backend(self, port, instance):
        raise NotImplementedError

    def remove_backend(self, port, instance):
        raise NotImplementedError

    def verify(self, listeners):
        raise NotImplementedError

section_name_prefix = ['global','listen','defaults','frontend','backend']
class ConfBuilderHaproxy(ConfBuilder):
    def __init__(self, source):
        ConfBuilder.__init__(self, source)
        self.__content_map = {} # key=section name(e.g, frontend), value: lines in the section
        cur_key=None
        for line in self.contents:
            key=line.strip('\n ').split(' ')[0]
            if key in section_name_prefix:
                cur_key = line.strip('\n ')
                self.__content_map[cur_key] = []
            elif cur_key is not None and len(line.strip('\n '))>0:
                self.__content_map[cur_key].append(line.strip('\n '))

    def build(self, destination=None):
        lines = []
        
        for prefix in section_name_prefix[:3]:  # assuming one-to-one mapping from prefix to config section
            section_name = None
            section_contents = None
            for key in self.__content_map.iterkeys():
                if key.startswith(prefix):
                    section_name = key
                    section_contents = self.__content_map[section_name]
            if section_contents is not None:
                lines.append('%s\n' % section_name)
                lines.extend(['  %s\n' % line for line in section_contents])  
                lines.append('\n')

        frontends = [ key for key in self.__content_map.iterkeys() if key.startswith('frontend') ]
        backends =  [ key for key in self.__content_map.iterkeys() if key.startswith('backend') ]
        for fe in frontends:
            lines.append('%s\n' % fe)
            lines.extend(['  %s\n' % line for line in self.__content_map[fe] ])
            lines.append('\n')
        
        for be in backends:
            lines.append('%s\n' % be)
            lines.extend(['  %s\n' % line for line in self.__content_map[be] ])
            lines.append('\n')
     
        if destination is None:
            return ''.join(lines)
        try:
            if os.path.exists(destination):
                os.unlink(destination)
            f=open(destination, "w")
            for line in lines:
                f.write(line)
            f.close()
        except Exception, err:
            raise err
             #  TODO: LOG ERROR

    @staticmethod
    def parse_key_value(line, delimiter=' '):
        line = line.strip(' ')
        if len(line.split(delimiter)) == 2:
            return line.split(delimiter)[0], line.split(delimiter)[1]
    
    def find_frontend(self, port):
        section_name = None
        section = []
        for key in self.__content_map.iterkeys():
            if key.strip(' ').startswith('frontend') and key.strip(' ').endswith('-%s' % port):
                section_name = key
                section = self.__content_map[key]
                break
        return (section_name, section)

    def find_backend_name(self, section):
        backend_name = None
        for line in section:
            if line.strip(' ').startswith('default_backend'):
                kv = ConfBuilderHaproxy.parse_key_value(line)
                if kv is not None:
                    backend_name = kv[1]
                    break
        return backend_name

    def add_protocol_port(self, protocol='tcp', port=80, cookie_name=None, cookie_expire=None, cert=None, comment=None):
        '''
            add new protocol/port to the config file. if there's existing one, pass
        '''
        if not ( protocol == 'http' or protocol == 'tcp' or protocol == 'https'):
            raise Exception('unknown protocol')

        # make sure no other frontend listen on the port
        for key in self.__content_map.iterkeys():
            key = key.strip(' ')
            if key.startswith('frontend') and key.endswith('-%s'%port):
                raise Exception('the port is found')
            
        section_name = 'frontend %s-%s' % (protocol,port)
        if not section_name in self.__content_map.iterkeys():
            self.__content_map[section_name]= [] 
            if comment is not None:
                self.__content_map[section_name].append('# %s'%comment)
            if protocol == 'https':
                self.__content_map[section_name].append('mode http')
            else:
                self.__content_map[section_name].append('mode %s' % protocol)
            if protocol == 'http' or protocol == 'https':
                self.__content_map[section_name].append('option forwardfor except 127.0.0.1')
            if protocol == 'https':
                self.__content_map[section_name].append('bind 0.0.0.0:%s ssl crt %s' % (port, cert))
            else: 
                self.__content_map[section_name].append('bind 0.0.0.0:%s' % port)

            if config.ENABLE_CLOUD_WATCH:  # this may have significant performance impact
                self.__content_map[section_name].append('log %s local2 info' % config.CW_LISTENER_DOM_SOCKET)
                if protocol == 'http' or protocol == 'https':
                    self.__content_map[section_name].append('log-format httplog\ %f\ %b\ %s\ %ST\ %ts\ %Tq\ %Tw\ %Tc\ %Tr\ %Tt') 
                elif protocol == 'tcp':
                    self.__content_map[section_name].append('log-format tcplog\ %f\ %b\ %s\ %ts\ %Tw\ %Tc\ %Tt') 

            def_backend = 'backend-%s-%s' % (protocol, port)
            self.__content_map[section_name].append('default_backend %s' % def_backend)
           
            if protocol == 'https':
                backend_attribute = 'mode http\n  balance roundrobin' 
            else:
                backend_attribute = 'mode %s\n  balance roundrobin' % protocol 
            if cookie_expire and cookie_name:
                servo.log.error('both duration-based and app-controlled cookie stickiness are enabled. something is wrong!')
            if ( protocol == 'http' or protocol == 'https' ) and cookie_expire:
                try:
                    cookie_expire = int(cookie_expire)
                    backend_attribute = '%s\n  cookie AWSELB insert indirect nocache maxidle %ds maxlife %ds' % (backend_attribute, cookie_expire, cookie_expire) 
                except exceptions.ValueError:
                    servo.log.error('failed to set cookie expiration: value is not a number type')
            elif ( protocol == 'http' or protocol == 'https' ) and cookie_name:
                backend_attribute = '%s\n  appsession %s len %d timeout %dm' % (backend_attribute, cookie_name, config.appcookie_length(), config.appcookie_timeout())

            # create the empty backend section
            self.__content_map['backend %s' % def_backend] = [backend_attribute]
        else:
            pass # do nothing

        return self
    
    def remove_protocol_port(self, port):
        '''
            remove existing port/protocol from the config if found
        '''
        (section_name, section) = self.find_frontend(port)
        if section_name is None:
            return self
        #remove the backend
        backend_name = self.find_backend_name(section)
        if backend_name is not None:
            backend = 'backend %s' % backend_name 
            if backend in self.__content_map.iterkeys():
                backend_conf = self.__content_map.pop(backend)
                del backend_conf[:]

        #remove the frontend
        frontend_conf = self.__content_map.pop(section_name)
        del frontend_conf[:]
        return self

    #instance = {hostname , port, protocol=None )
    def add_backend(self, port, instance):
        (section_name, section) = self.find_frontend(port)
        if section_name is None:
            return self
        
        backend_name = self.find_backend_name(section)
        if backend_name is None:
            return self

        backend = 'backend %s' % backend_name 
        if backend not in self.__content_map.iterkeys():
            raise 'no backend is found with name %s' % backend_name

        backend_conf = self.__content_map[backend]
        lbcookie_enabled = False
        appcookie_enabled = False
        if any("cookie AWSELB" in s for s in backend_conf):
            lbcookie_enabled = True
        elif any("appsession " in s for s in backend_conf):
            appcookie_enabled = True

        line = 'server %s %s:%d' % (section_name.replace('frontend','').strip(' '), instance['hostname'], instance['port'])
        if lbcookie_enabled or appcookie_enabled:
            line = line + ' cookie %s' % ConfBuilderHaproxy.encode_str(instance['hostname'])
       
        backend_conf.insert(0, line)
        return self

    @staticmethod
    def encode_str(server):
        return base64.b64encode(server) 

    def remove_backend(self, port, instance):
        section_name, section = self.find_frontend(port)
        if section_name is None:
            return self
        
        backend_name = self.find_backend_name(section)
        if backend_name is None:
            return self

        backend = 'backend %s' % backend_name 
        if backend in self.__content_map.iterkeys():
            backend_conf = self.__content_map.pop(backend)  
            line = 'server %s %s:%d' % (section_name.replace('frontend','').strip(' '), instance['hostname'], instance['port'])
            backend_conf.remove(line)
        return self
