#!/usr/bin/env python2.7


from __future__ import print_function

import os
import sys
import re
import xdg.BaseDirectory
import xdg.DesktopEntry
import glob
import gtk

global subclasses
global _hashed_subclasses
global aliases
global _hashed_aliases

subclasses = {}
_hashed_subclasses = False
aliases = {}
_hashed_aliases = False



# this is a crude translation of File::DesktopEntry(3pm)


class DesktopEntryIsNotAnApplication(Exception):
	pass

class DesktopEntryExecFormatError(Exception):
	pass

class RegexSubst(object):
	"""
	An object remembering what was matched during the regexp substitution.
	The constructor is very similar to the re.sub() one,
	but does not handle group references (eg. "\\1") in 'replacement' parameter.
	You probably want to invoke it by count=1 keyword argument.
	"""
	def __init__(self, pattern, replacement, string, **kwargs):
		self.match = None
		self.replacement = replacement
		self.result = re.sub(pattern, self.replacer, string, **kwargs)
	def replacer(self, match):
		self.match = match
		return self.replacement
	def group(self, gnum=0):
		if self.match is None:
			return None
		try:
			return self.match.group(gnum)
		except IndexError:
			return None

class DesktopEntry(xdg.DesktopEntry.DesktopEntry):
	def __repr__(self):
		return "<%s file=\"%s\">" % (self.__class__.__name__, self.filename)
	
	def icon_file(self, preferred_size):
		iconpath = None
		iconname = self.getIcon()
		if iconname:
			preferred_size_px = gtk.icon_size_lookup(preferred_size)[0]
			if iconname.startswith('/'):
				iconpath = iconname
			else:
				icondirs = []
				for c in 'hicolor', 'locolor', 'gnome':
					icondir = "/usr/share/icons/" + c
					smallicondirs = []
					subdirs = [{'path': path, 'size': re.search(r'/([0-9]+)x([0-9]+)', path).group(1)} for path in glob.glob(icondir+'/*x*/*')]
					subdirs.sort(key = lambda it: it['size'])
					for subdir in subdirs:
						if subdir['size'] < preferred_size:
							smallicondirs.insert(0, subdir['path'])
						else:
							icondirs.append(subdir['path'])
					icondirs.extend(glob.glob(icondir+'/scalable/*'))
					for subdir in smallicondirs:
						icondirs.append(subdir)
				icondirs.append('/usr/share/pixmaps')
				
				for icondir in icondirs:
					for iconext in 'png', 'xpm', 'svg':
						if os.path.extsep in iconname:
							iconpath_test = os.path.join(icondir, iconname)
						else:
							iconpath_test = os.path.join(icondir, iconname + os.path.extsep + iconext)
						if os.path.isfile(iconpath_test):
							iconpath = iconpath_test
							break
						elif os.path.extsep in iconname:
							break
					if iconpath is not None:
						break
		return iconpath
	
	def _split(self, s):
		"""
		Reverse quoting and break string in words.
		It allows single quotes to be used, which the spec doesn't.
		"""
		args = []
		while re.search(r'\S', s):
			match = re.match('^([\'"])', s)
			if match:
				q = match.group(1);
				sub = RegexSubst(r'^(' + q + r'(\\.|[^' + q + r'])*' + q + r')', '', s, count=1, flags=re.S)
				s = sub.result
				if sub.group(1) is not None:
					args.append(sub.group(1))
			sub = RegexSubst(r'(\S*)\s*', '', s, count=1)  # also fallback for above regex
			s = sub.result
			if sub.group(1) is not None:
				args.append(sub.group(1))
		args = [arg for arg in args if len(arg or '')]
		for arg in args:
			match = re.match('^(["\'])(.*)'+r'\1$', arg, flags=re.S)
			if match:
				arg = match.group(2)
				arg = re.sub(r'\\(["`\$\\])', lambda m: m.group(1))  # remove backslashes
		return args
	
	def _quote(self, words):
		"""
		Turn a list of words in a properly quoted Exec key
		"""
		qwords = []
		for word in words:
			if word is None: continue
			match = re.search('([\s"\'`'+r'\\<>~\|\&;\$\*\?#\(\)])', word)  # reserved chars
			if match:
				qword = re.sub(r'(["`\$\\])', lambda m: '\\'+m.group(1), word)  # add backslashes
				qword = '"' + qword + '"'  # add quotes
			else:
				qword = word
			qwords.append(qword)
		return ' '.join(qwords)
	
	def _uri_to_path(self, uri):
		import urllib2
		x = uri.encode('utf8')
		x = urllib2.unquote(x)
		return x.decode('utf8')
	
	def _path_to_uri(self, path):
		import urllib2
		path = os.path.abspath(path)
		prefix, filename = os.path.split(path)
		uri = '/'.join([urllib2.quote(path_element) for path_element in os.path.join(prefix, filename).split(os.path.sep)])
		return uri
	
	def _paths(self, args):
		"""
		Check if we need to convert file:// uris to paths
		support file:/path file://localhost/path and file:///path
		A path like file://host/path is replace by smb://host/path
		which the app probably can't open
		"""
		for arg in args:
			sub = RegexSubst(r'^file:(?://localhost/+|/|///+)(?!/)', '/', arg, count=1, flags=re.I)
			if sub.match:
				arg = sub.result
				arg = self._uri_to_path(arg)
			arg = re.sub(r'^file://(?!/)', 'smb://', arg, count=1, flags=re.I)
			yield arg
	
	def _dirs(self, args):
		"""
		Like _paths, but makes the path a directory
		"""
		for path in self._paths(args):
			if os.path.isdir(path):
				yield path
			else:
				prefix, filename = os.path.split(path)
				yield prefix
	
	def _uris(self, args):
		"""
		Convert paths to file:// uris
		"""
		for arg in args:
			if re.search(r'^(mailto:|\w+://)', arg):  # File::DesktopEntry(3pm) 0.22 does not take "mailto:" URLs into account, only searches "^\w+://" here.
				yield arg
			else:
				yield 'file://' + self._path_to_uri(arg)
	
	def expand_format_code(self, code, args):
		if   code == '%': return '%'
		elif code == 'f': return first(self._paths(args))
		elif code == 'u': return first(self._uris(args))
		elif code == 'd': return first(self._dirs(args))
		elif code == 'c': return self.getName()
		elif code == 'k': return self.filename
		return ''
	
	def parse_Exec(self, args, wantarray=False):
		format = self._split(self.getExec())
		
		# Check format
		seen = 0
		for s in format:
			s = s.replace('%%', '')
			if re.search(r'%[fFuUdD]', s):
				seen += 1
			
			if not re.search(r'^%[FUD]$', s) and re.search(r'%[FUD]', s):
				raise DesktopEntryExecFormatError("Exec key for '%s' contains '%%F', '%%U' or '%%D' at the wrong place." % (self.getName(),))
			match = re.search(r'(%[^fFuUdDnNickvm])', s)
			if match:
				raise DesktopEntryExecFormatError("Exec key for '%s' contains unknown field code '%s'." % (self.getName(), match.group(1),))
			if len(args) > 1 and re.search(r'%[fud]', s):
				raise DesktopEntryExecFormatError("Application '%s' takes only one argument, not %d." % (self.getName(), len(args),))
			if re.search(r'%[nNvm]', s):
				print("Exec key for '%s' contains deprecated field codes.\n" % (self.getName(),), file=sys.stderr)
		if seen == 0:
			format.append('%F')
		elif seen > 1:
			# not allowed according to the spec
			print("Exec key for '%s' contains multiple fields for files or uris.\n" % (self.getName(),), file=sys.stderr)
		
		execargs = []
		
		for s in format:
			match = re.match(r'^%([FUD])$', s)
			if match:
				fmtcode = match.group(1)
				if fmtcode == 'F':
					x = self._paths(args)
				elif fmtcode == 'U':
					x = self._uris(args)
				else:
					x = self._dirs(args)
				execargs.extend(x)
			elif s == '%i':
				icon = self.get('Icon')
				if icon is not None:
					execargs.extend(['--icon', icon])
			else:  # expand with word ( e.g. --input=%f )
				s = re.sub(r'%(.)', lambda m: self.expand_format_code(m.group(1), args), s)
				execargs.append(s)
		
		return execargs if wantarray else self._quote(execargs)
	
	def execargs(self, args):
		if self.getType() != 'Application':
			raise DesktopEntryIsNotAnApplication()
		
		execargs = self.parse_Exec(args, wantarray=True)
		
		if self.getTerminal():
			execargs = self._split(os.environ.get('TERMINAL', 'x-terminal-emulator -e')) + execargs
		
		return execargs
	
	def run(self, args, exec_cb):
		execargs = self.execargs(args)
		
		cwd = None
		path = self.getPath()
		if path:
			cwd = os.getcwd()
			os.chdir(path)  # let it raise an exception
			os.environ['PWD'] = path
			print("Running from directory: %s\n" % path, file=sys.stderr)
		
		exec_cb(execargs)
		
		if cwd is not None:
			os.chdir(cwd)
			os.environ['PWD'] = cwd


# this is a crude translation of File::MimeInfo::Applications(3pm)


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
			return DesktopEntry(path)
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
	for parent in mimetype_isa(mimetype):
		for app in mime_applications(parent):
			if app is not None:
				apps.append(app)
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
			lst.append(DesktopEntry(path))
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
