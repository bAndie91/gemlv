#!/usr/bin/env python2

import os

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
	if error_handler is None:
		import gemlv.sysutils
		error_handler = lambda e: gemlv.sysutils.warnx(str(e))
	abook_files = get_paths()
	if abook_files:
		for abook_path in abook_files:
			try:
				for ln in open(abook_path, 'r'):
					callback(ln.strip(), userdata)
			except IOError as e:
				error_handler(e)
	else:
		e = gettext("There is no addressbook file. Create one in ~/Mail/.addressbook.d/ directory.")
		error_handler(e)
		return False
	return True

def get_full():
	abook = []
	load(callback = lambda addr, abook: abook.append(addr), userdata=abook)
	return abook

def add(email, section, address_line=None):
	if address_line is None: address_line = email
	addresses = get_addressbook_full()
	# TODO: update matching line! (the contact changed her real name)
	if all(addr[1] != email for addr in gemlv.utils.getaddresses(addresses)):
		path = os.path.join(get_directory_path(), section)
		with open(path, 'a') as fh:
			fh.write(address_line+'\n')
