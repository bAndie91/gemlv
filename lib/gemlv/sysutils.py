#!/usr/bin/env python2

import os
import sys
import ctypes
from ctypes.util import find_library
import fcntl
import re


def warnx(string):
	sys.stderr.write(string + ('' if string[-1] == '\n' else '\n'))

class TIMEVAL(ctypes.Structure):
	_fields_ = [('tv_sec', ctypes.c_long), ('tv_usec', ctypes.c_long)]

def futimes(fd, times):
	if len(times) < 2:
		raise OSError(os.errno.EINVAL)
	stdlib = find_library('c')
	libc = ctypes.CDLL(stdlib)
	TIMEVALS = TIMEVAL * 2
	if libc.futimes(fd, TIMEVALS((times[0], 0), (times[1], 0))) == -1:
		raise OSError()

def recursive_rm(path):
	try:
		try:
			os.unlink(path)
		except OSError as e:
			if e.errno == os.errno.EISDIR:
				for x in os.listdir(path):
					recursive_rm(os.path.join(path, x))
				os.rmdir(path)
			else:
				raise
	except OSError as e:
		warnx(str(e))

def set_blocking(fd, doblock):
	if type(fd) != int:
		fd = fd.fileno()
	fl = fcntl.fcntl(fd, fcntl.F_GETFL)
	if doblock:
		fl = fl & ~os.O_NONBLOCK
	else:
		fl = fl | os.O_NONBLOCK
	return fcntl.fcntl(fd, fcntl.F_SETFL, fl)

def is_executable(p):
	return (os.path.isfile(p) and os.access(p, os.X_OK))

def which(cmd):
	ap, bn = os.path.split(cmd)
	if ap:
		if is_executable(cmd):
			return cmd
	else:
		for d in os.environ['PATH'].split(os.path.pathsep):
			p = os.path.join(d, cmd)
			if is_executable(p):
				return p
	return None

def mkdir(path):
	if os.path.exists(path) or path == '':
		return
	else:
		mkdir(os.path.dirname(path))
		os.mkdir(path)

def is_safe_symlink(target, root):
	"""
	Return True if target is within root or target itself is root.
	target and root are absolute paths.
	"""
	assert os.path.isabs(target)
	assert os.path.isabs(root)
	sep = re.escape(os.path.sep)
	par = re.escape(os.path.pardir)
	return not bool(re.search('(^|'+sep+')'+par+'('+sep+'|$)', os.path.relpath(target, root)))

def read_symlink_target_abs(symlink):
	assert os.path.isabs(symlink)
	target = os.readlink(symlink)
	if os.path.isabs(target):
		return target
	else:
		return os.path.normpath(os.path.join(symlink, os.path.pardir, target))

def make_relative_symlink(point_to, symlink_path):
	assert os.path.isabs(point_to)
	return os.path.relpath(point_to, os.path.join(symlink_path, os.path.pardir))

def basenameify(s):
	"""
	Replace ASCII slash (/) to a similar-looking multibyte char (U+2215 DIVISION SLASH)
	"""
	return s.replace('/', u'\u2215')

def file_uri_to_path(uri):
	if uri.startswith('file:///'):
		return urllib2.unquote(uri[7:])
	elif uri.startswith('file://'):
		return urllib2.unquote(uri[6:])
	elif uri.startswith('file:/'):
		return urllib2.unquote(uri[5:])
	return None
