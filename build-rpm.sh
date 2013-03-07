#!/bin/bash

JENKINS_URL=${JENKINS_URL:-http://jenkins.release.eucalyptus-systems.com}

if [ ! -d ./rpmfab ]; then
    git clone git://github.com/gholms/rpmfab.git
fi

rpmfab/build-arch.py \
    -c $JENKINS_URL/userContent/mock/balancer-centos-6-x86_64.cfg -o results \
    --mock-options "--uniqueext $BUILD_TAG" *.src.rpm


