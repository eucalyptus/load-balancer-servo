#!/bin/bash
#
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

function insert_global()
{
    local spec=$1
    local var=$2
    local value=$3

    sed -i "1s/^/# This is a generated value\n%global $var $value\n\n/" $spec
}

. scripts/buildenv.sh

[ -d ./build ] && rm -rf build

mkdir -p build/{BUILD,BUILDROOT,SRPMS,RPMS,SOURCES,SPECS}

TARBALL_NAME=load-balancer-servo-$BUILD_VERSION

cp *.spec build/SPECS
git archive --format=tar --prefix=$TARBALL_NAME/ HEAD | gzip > build/SOURCES/$TARBALL_NAME.tar.gz

SPECFILE=$(echo -n build/SPECS/*.spec)

insert_global $SPECFILE dist .el6
insert_global $SPECFILE build_id $BUILD_ID
insert_global $SPECFILE build_num $BUILD_NUMBER

rpmbuild --define "_topdir `pwd`/build" \
    --nodeps -bs build/SPECS/load-balancer-servo.spec || exit 1

[ ! -d ./rpmfab ] && git clone git://github.com/gholms/rpmfab.git

./rpmfab/build-arch.py -c $JENKINS_URL/userContent/mock/centos-6-x86_64.cfg \
    -o ./results build/SRPMS/*.src.rpm

