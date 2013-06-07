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

BUILD_NUMBER=${BUILD_NUMBER:-0}

if [ -z "$GIT_COMMIT" ]; then
    GIT_COMMIT_SHORT=`git rev-parse --short HEAD`
else
    GIT_COMMIT_SHORT=${GIT_COMMIT:0:7}
fi

if [ "x$BUILD_RELEASE" = "xtrue" ]; then
    BUILD_ID=$BUILD_NUMBER
else
    BUILD_ID=$BUILD_NUMBER.$(date +%y%m%d)git${GIT_COMMIT_SHORT}
fi

BUILD_VERSION=$(cat VERSION)

