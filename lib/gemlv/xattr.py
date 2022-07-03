#!/usr/bin/env python

from __future__ import absolute_import
import os
try:
	import xattr
except ImportError:
	xattr = None
from gemlv.sysutils import warnx
import gettext


def get(file_, attrname):
	if xattr is not None:
		try:
			return xattr.getxattr(file_, attrname)
		except IOError as e:
			if e.errno not in [os.errno.ENODATA, os.errno.ENOTSUP, os.errno.ENOSYS]:
				raise
	return None

def append(fh, attrs, filename='-', glue=''):
	attrs = attrs.copy()
	for attr in attrs.keys():
		curr_value = get(fh, attr)
		if curr_value is not None:
			attrs[attr] = curr_value + glue + attrs[attr]
	return set(fh, attrs, filename)

def set(fh, attrs, filename='-'):
	allok = False
	if xattr is not None:
		allok = True
		for attrname, attrval in attrs.iteritems():
			try:
				if attrval is None:
					xattr.removexattr(fh, attrname)
				elif attrval:  # not set empty value
					xattr.setxattr(fh, attrname, attrval)
			except IOError as e:
				if e.errno == os.errno.ENODATA and attrval is None:
					# Ignore that a nonexistent attribute could not be removed
					pass
				else:
					warnx(gettext.gettext("Notice: can not set xattr '%s' on '%s': %s") % (attrname, filename, str(e)))
					allok = False
					if e.errno not in [os.errno.ENODATA, os.errno.ENOTSUP, os.errno.ENOSYS]:
						raise
	return allok

def supported():
	return xattr is not None
