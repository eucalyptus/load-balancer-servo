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

TARBALL_NAME=load-balancer-servo-1.0.0
BUILD_NUMBER=${BUILD_NUMBER:-0}

if [ -z "$GIT_COMMIT" ]; then
    GIT_COMMIT_SHORT=`git rev-parse --short HEAD`
else
    GIT_COMMIT_SHORT=${GIT_COMMIT:0:7}
fi

BUILD_ID=$BUILD_NUMBER.$(date +%y%m%d)git${GIT_COMMIT_SHORT}

[ -d ./build ] && rm -rf build

rm -f *.src.rpm

mkdir -p build/{BUILD,BUILDROOT,SRPMS,RPMS,SOURCES,SPECS}

cp *.spec build/SPECS

git archive --format=tar --prefix=$TARBALL_NAME/ HEAD | gzip > build/SOURCES/$TARBALL_NAME.tar.gz

rpmbuild --define "_topdir `pwd`/build" --define "dist .el6" \
    --define "build_id $BUILD_ID" \
    -bs build/SPECS/load-balancer-servo.spec

mv build/SRPMS/*.src.rpm .

