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
import servo
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

    def add(self, protocol, port, instances=[], comment=None):
        try:
            self.addProtocolPort(protocol, port, comment )
            for instance in instances:
                self.addBackend(port, instance)
        except Exception, err:
            servo.log.error('failed to add protocol-port: %s' % err)
        return self

    def addProtocolPort(self, protocol, port):
        raise NotImplementedError
  
    def removeProtocolPort(self, port):
        raise NotImplementedError

    def addBackend(self, port, instance):
        raise NotImplementedError

    def removeBackend(self, port, instance):
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
    def parseKeyValue(line, delimiter=' '):
        line = line.strip(' ')
        if len(line.split(delimiter)) == 2:
            return line.split(delimiter)[0], line.split(delimiter)[1]
    
    def findFrontend(self, port):
        section_name = None
        section = []
        for key in self.__content_map.iterkeys():
            if key.strip(' ').startswith('frontend') and key.strip(' ').endswith('-%s' % port):
                section_name = key
                section = self.__content_map[key]
                break
        return (section_name, section)

    def findBackendName(self, section):
        backend_name = None
        for line in section:
            if line.strip(' ').startswith('default_backend'):
                kv = ConfBuilderHaproxy.parseKeyValue(line)
                if kv is not None:
                    backend_name = kv[1]
                    break
        return backend_name

    def addProtocolPort(self, protocol='tcp', port=80, comment=None):
        '''
            add new protocol/port to the config file. if there's existing one, pass
        '''
        if not ( protocol == 'http' or protocol == 'tcp'):
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
            self.__content_map[section_name].append('mode %s' % protocol)
            self.__content_map[section_name].append('bind 0.0.0.0:%s' % port)
            def_backend = 'backend-%s-%s' % (protocol, port)
            self.__content_map[section_name].append('default_backend %s' % def_backend)
            # create the empty backend section
            self.__content_map['backend %s' % def_backend] = ['balance roundrobin']
        else:
            pass # do nothing

        return self
    
    def removeProtocolPort(self, port):
        '''
            remove existing port/protocol from the config if found
        '''
        (section_name, section) = self.findFrontend(port)
        if section_name is None:
            return self
        #remove the backend
        backend_name = self.findBackendName(section)
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
    def addBackend(self, port, instance):
        (section_name, section) = self.findFrontend(port)
        if section_name is None:
            return self
        
        backend_name = self.findBackendName(section)
        if backend_name is None:
            return self

        backend = 'backend %s' % backend_name 
        if backend not in self.__content_map.iterkeys():
            self.__content_map[backend] = ['balance roundrobin']
        backend_conf = self.__content_map[backend]
        line = 'server %s %s:%d' % (section_name.replace('frontend','').strip(' '), instance['hostname'], instance['port'])
        backend_conf.insert(0, line)
        return self

    def removeBackend(self, port, instance):
        section_name, section = self.findFrontend(port)
        if section_name is None:
            return self
        
        backend_name = self.findBackendName(section)
        if backend_name is None:
            return self

        backend = 'backend %s' % backend_name 
        if backend in self.__content_map.iterkeys():
            backend_conf = self.__content_map.pop(backend)  
            line = 'server %s %s:%d' % (section_name.replace('frontend','').strip(' '), instance['hostname'], instance['port'])
            backend_conf.remove(line)
        return self
