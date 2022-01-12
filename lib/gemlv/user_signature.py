#!/usr/bin/env python2

import os
from gemlv.utils import get_gecos_name
import re
import traceback
from glob import glob

def base_path():
	return os.path.join(os.environ['HOME'], 'Mail', '.signatures')

def default_path():
	return os.path.join(os.environ['HOME'], '.signature')

def fmt(s):
	return re.sub('\n?$', '\n', s)

def default():
	try:
		sign = open(default_path(), 'r').read()
	except IOError as e:
		traceback.print_exc(e)
		sign = '--\n' + get_gecos_name() + '\n'
	return fmt(sign)

def iter_all():
	yield None  # this one means the default signature
	for path in glob(base_path() + os.path.sep + '*'):
		yield os.path.basename(path)

def byname(name):
	if name is None:
		return default()
	sign = open(base_path() + os.path.sep + name, 'r').read()
	return fmt(sign)

