#!/usr/bin/env python2

import os
import gemlv.utils
from gemlv.sysutils import mkdir

def get_singlefile_path():
	return os.path.join(os.environ['HOME'], 'Mail', '.addressbook')

def get_directory_path():
	return os.path.join(os.environ['HOME'], 'Mail', '.addressbook.d')

def get_paths():
	files = []
	default_abook_file_path = get_singlefile_path()
	if os.path.exists(default_abook_file_path):
		files.append(default_abook_file_path)
	def file_found(files, dirname, entries):
		for entryname in entries:
			entrypath = os.path.join(dirname, entryname)
			if os.path.isfile(entrypath):
				files.append(entrypath)
	os.path.walk(get_directory_path(), file_found, files)
	return files

def load(callback, userdata = None, error_handler = None, gettext = str):
	"""
	callback is a function.
	arguments of the callback function:
	- next line from the address book (string)
	- userdata object
	if the callback returns True then the loading process stops.
	other return values does not stop the loading process.
	"""
	if error_handler is None:
		import gemlv.sysutils
		error_handler = lambda e: gemlv.sysutils.warnx(str(e))
	abook_files = get_paths()
	if abook_files:
		stop = False
		for abook_path in abook_files:
			try:
				for ln in open(abook_path, 'r'):
					cb_resp = callback(ln.strip(), userdata)
					if cb_resp is True:
						stop = True
						break
			except IOError as e:
				error_handler(e)
			if stop:
				break
	else:
		e = gettext("There is no addressbook file. Create one in ~/Mail/.addressbook.d/ directory.")
		error_handler(e)
		return False
	return True

def get_full():
	abook = {}
	load(callback = lambda addr, abook: abook.__setitem__(addr, True), userdata=abook)
	return abook.keys()

def add(section, address_line=None):
	"add the given address line to the addressbook unless an entry with the same realname and email address is already there (in any addressbook section)"
	addresses = get_full()
	if any(al.email == address_line.email and (al.realname == address_line.realname or address_line.realname == '') for al in gemlv.utils.getaddresslines(addresses)):
		pass
	else:
		path = os.path.join(get_directory_path(), section)
		with open(path, 'a') as fh:
			fh.write(address_line.addressline+'\n')

def create(section):
	path = os.path.join(get_directory_path(), section)
	mkdir(os.path.dirname(path))
	open(path, 'a').close()
