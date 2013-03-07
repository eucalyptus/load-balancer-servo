#!/bin/bash

TARBALL_NAME=load-balancer-servo-1.0.0

[ -d ./build ] && rm -rf build

rm -f *.src.rpm

mkdir -p build/{BUILD,BUILDROOT,SRPMS,RPMS,SOURCES,SPECS}

cp *.spec build/SPECS

git archive --format=tgz --prefix=$TARBALL_NAME/ HEAD > build/SOURCES/$TARBALL_NAME.tar.gz

rpmbuild --define "_topdir `pwd`/build" --define "dist .el6" \
    -bs build/SPECS/load-balancer-servo.spec

mv build/SRPMS/*.src.rpm .

