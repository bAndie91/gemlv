#!/usr/bin/env python2.7

import os
import sys
import re
import xdg.BaseDirectory

global subclasses = {}
global _hashed_subclasses = False
global aliases = {}
global _hashed_aliases = False

def mimetype_canon(mimetype):
	if not _hashed_aliases:
		rehash_aliases()
	return aliases[mimetype] if mimetype in aliases else mimetype

def rehash_aliases():
	aliases = _read_map_files('aliases')
	_hashed_aliases = True

def first(generatorinstance):
	try:
		return generatorinstance.next
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

class DesktopEntry(object):
	def __init__(self, patH):
		self.path = path

def _find_file(lst)
	for basename in lst:
		path = first(data_files(os.path.join('applications', basename)))
		if path is not None:
			return DesktopEntry(path)
	return None

def _read_map_files(name, lst=None):
	paths = reversed(data_files("mime/"+name))
	mapp = {}
	done = {}
	for path in paths:
		if path in done: continue
		with open(path, 'r') as fh:
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
	return [_default(mime)] + _others(mime)
}

def mime_applications_all(mimetype)
	apps = []
	apps.extend(mime_applications(mimetype))
	apps.extend([mime_applications(m) for m in mimetype_isa(mimetype)])
	return apps

def _default(mimetype):
	user = os.path.join(xdg.BaseDirectory.xdg_config_home, 'mimeapps.list')
	system = first(config_dirs('mimeapps.list'))
	deprecated = os.path.join(xdg.BaseDirectory.xdg_data_home, 'applications', 'mimeapps.list')
	distro = first(os.path.join('applications', 'mimeapps.list'))
	legacy = os.path.join(xdg.BaseDirectory.xdg_data_home, 'applications', 'defaults.list')
	
	if not any(path is not None and os.path.isfile(path) and os.access(path, os.R_OK) for path in user, system, deprecated, distro, legacy):
		return None
	
	paths = [p for p in mimetype, user, system, deprecated, distro, legacy if p is not None]
	lst = _read_list(paths)
	desktop_file = _find_file(reversed(lst))
	return desktop_file
}

sub _others {
	my $mimetype = shift;

	$Carp::CarpLevel++;
	my (@list, @done);
	for my $dir (data_dirs('applications')) {
		my $cache = File::Spec->catfile($dir, 'mimeinfo.cache');
		next if grep {$_ eq $cache} @done;
		push @done, $cache;
		next unless -f $cache and -r _;
		for (_read_list($mimetype, $cache)) {
			my $file = File::Spec->catfile($dir, $_);
			next unless -f $file and -r _;
			push @list, File::DesktopEntry->new($file);
		}
	}
	$Carp::CarpLevel--;

	return @list;
}

sub _read_list { # read list with "mime/type=foo.desktop;bar.desktop" format
	my $mimetype = shift;

	my @list;
	my $succeeded;

	for my $file (@_) {
		if (open LIST, '<', $file) {
			$succeeded = 1;
			while (<LIST>) {
				/^\Q$mimetype\E=(.*)$/ or next;
				push @list, grep defined($_), split ';', $1;
			}
			close LIST;
		}
	}

	unless ($succeeded) {
		croak "Could not read any defaults, tried:\n" . join("\t\n", @_);
	}

	return @list;
}
