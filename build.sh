#!/bin/bash

set -e

version=$(git describe --tags)

mkdir -p deb/DEBIAN
mkdir -p deb/etc/gemlv
mkdir -p deb/usr/bin
mkdir -p deb/usr/lib/python2.7/dist-packages/gemlv
mkdir -p deb/usr/libexec/gemlv

cp -va ./DEBIAN/* deb/DEBIAN/
cp -va ./usr/* deb/usr/
cp -va ./lib/gemlv/*.py deb/usr/lib/python2.7/dist-packages/gemlv/
cp -va ./gemlv deb/usr/bin/
ln -snvf gemlv deb/usr/bin/gemlv-compose
ln -snvf gemlv deb/usr/bin/gemlv-mailto
cp -va ./gemlv-report* deb/usr/bin/
cp -va ./scan-participants deb/usr/libexec/gemlv/
cp -va ./filters.conf deb/etc/gemlv/

for d in ./usr/share/locale/*/LC_MESSAGES
do
	(
		set -e
		cd "$d"
		msgfmt -o gemlv.mo gemlv.po
	)
done

echo Version: $version >&2
cat DEBIAN/control.skel | sed -e "s/^Version:.*/Version: $version/" > deb/DEBIAN/control
