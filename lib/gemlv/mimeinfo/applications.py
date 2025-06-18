#!/usr/bin/env python2.7

from __future__ import print_function

import os
import sys
import re
import xdg.BaseDirectory
import xdg.DesktopEntry

global subclasses
global _hashed_subclasses
global aliases
global _hashed_aliases

subclasses = {}
_hashed_subclasses = False
aliases = {}
_hashed_aliases = False

def mimetype_canon(mimetype):
	if not _hashed_aliases:
		rehash_aliases()
	return aliases[mimetype] if mimetype in aliases else mimetype

def rehash_aliases():
	aliases = _read_map_files('aliases')
	_hashed_aliases = True

def first(generatorinstance):
	try:
		return generatorinstance.next()
	except StopIteration:
		return None

def data_files(basename):
	for it in _find_files(basename, os.path.isfile, [xdg.BaseDirectory.xdg_data_home] + xdg.BaseDirectory.xdg_data_dirs):
		yield it

def data_dirs(basename):
	for it in _find_files(basename, os.path.isdir, [xdg.BaseDirectory.xdg_data_home] + xdg.BaseDirectory.xdg_data_dirs):
		yield it

def config_dirs(basename):
	for it in _find_files(basename, os.path.isdir, [xdg.BaseDirectory.xdg_config_home] + xdg.BaseDirectory.xdg_config_dirs):
		yield it

def _find_files(basename, typechecker, dirs):
	for dir in dirs:
		path = os.path.join(dir, basename)
		if typechecker(path) and os.access(path, os.R_OK):
			yield path

def _find_file(lst):
	for basename in lst:
		path = first(data_files(os.path.join('applications', basename)))
		if path is not None:
			return xdg.DesktopEntry.DesktopEntry(path)
	return None

def _read_map_files(name, lst=None):
	paths = reversed(list(data_files("mime/"+name)))
	mapp = {}
	done = {}
	for path in paths:
		if path in done: continue
		try:
			fh = open(path, 'r')
		except IOError:
			pass
		else:
			with fh:
				for line in fh.readlines():
					line = line.strip()
					if line.startswith('#'): continue
					(k, v) = re.split(r'\s+', line, 1)
					if lst:
						if k not in mapp:
							mapp[k] = []
						mapp[k].append(v)
					else:
						mapp[k] = v
		done[path] = True
	return mapp

def rehash_subclasses():
	subclasses = _read_map_files('subclasses', 'LIST')
	_hashed_subclasses = True

def mimetype_isa(mimetype, parent=None):
	#if (ref $mimet or ! defined $mimet) {
	#	$mimet = mimetype_canon($parent);
	#	undef $parent;
	#}
	#else {
	mimetype = mimetype_canon(mimetype)
	parent = mimetype_canon(parent)
	if not _hashed_subclasses:
		rehash_subclasses()
	
	subc = []
	if mimetype == 'inode/mount-point':
		subc.append('inode/directory')
	if mimetype in subclasses:
		subc.extend(subclasses[mimetype])
	if mimetype.startswith('text/'):
		subc.append('text/plain')
	if not mimetype.startswith('inode/'):
		subc.append('application/octet-stream')

	if parent:
		return len([True for x in subc if x == parent])
	else:
		return subc

def mime_applications(mimetype):
	mime = mimetype_canon(mimetype)
	return [a for a in [_default(mime)] + _others(mime) if a is not None]

def mime_applications_all(mimetype):
	apps = []
	apps.extend(mime_applications(mimetype))
	apps.extend([a for a in [mime_applications(m) for m in mimetype_isa(mimetype)] if n is not None])
	return apps

def _default(mimetype):
	user = os.path.join(xdg.BaseDirectory.xdg_config_home, 'mimeapps.list')
	system = first(config_dirs('mimeapps.list'))
	deprecated = os.path.join(xdg.BaseDirectory.xdg_data_home, 'applications', 'mimeapps.list')
	distro = first(data_dirs(os.path.join('applications', 'mimeapps.list')))
	legacy = os.path.join(xdg.BaseDirectory.xdg_data_home, 'applications', 'defaults.list')
	
	if not any(path is not None and os.path.isfile(path) and os.access(path, os.R_OK) for path in (user, system, deprecated, distro, legacy)):
		return None
	
	paths = [p for p in user, system, deprecated, distro, legacy if p is not None]
	lst = _read_list(mimetype, paths)
	desktop_file = _find_file(reversed(lst))
	return desktop_file

def _others(mimetype):
	lst = []
	done = {}
	for dir in data_dirs('applications'):
		cache = os.path.join(dir, 'mimeinfo.cache')
		if cache in done: continue
		done[cache] = True
		if not (os.path.isfile(cache) and os.access(cache, os.R_OK)): continue
		for file in _read_list(mimetype, [cache]):
			path = os.path.join(dir, file)
			if not (os.path.isfile(path) and os.access(path, os.R_OK)): continue
			lst.append(xdg.DesktopEntry.DesktopEntry(path))
	return lst

def _read_list(mimetype, paths):
	"""
	read list with "mime/type=foo.desktop;bar.desktop" format
	"""
	
	lst = []
	succeeded = False
	
	for path in paths:
		try:
			fh = open(path, 'r')
		except IOError:
			pass
		else:
			with fh:
				succeeded = True
				for line in fh.readlines():
					line = line.strip()
					match = re.match(r'^'+re.escape(mimetype)+r'=(.*)$', line)
					if match:
						lst.extend(match.group(1).split(';'))
	
	if not succeeded:
		print("Could not read any defaults, tried:\n" + "\t\n".join(paths), file=sys.stderr)

	return lst
