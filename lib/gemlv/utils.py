#!/usr/bin/env python2

from __future__ import absolute_import
import re
import email
import pwd
import os
from gemlv.constants import *

def fix_unquoted_comma(s):
	"""Many MUA do not enclose real names which contain comma, in double quotes.
	This causes issues in splitting address lines into individual addesses.
	Try to work around this."""
	def repl(m):
		probably_realname = m.group(2)
		probably_realname_norm = probably_realname.strip()
		if probably_realname_norm == '' or probably_realname_norm.startswith('"') or probably_realname.find(',')==-1:
			return m.group(0)
		else:
			return '%s "%s" %s' % (m.group(1), probably_realname_norm, m.group(3))  # @notranslate
	return re.sub('(^|,)(.+)(<)', repl, s)

def getaddresses(array):
	return filter(lambda a: a[1] != '', email.utils.getaddresses(map(fix_unquoted_comma, array)))

def getaddresslines(array, eml=None):
	return map(lambda t: AddressLine(t, eml=eml), getaddresses(array))

def headercase(s):
	return re.sub(r'\b(.)', lambda x: x.group(1).upper(), s.lower())

def get_gecos_name():
	return re.sub(',.*,.*,.*', '', pwd.getpwuid(os.getuid()).pw_gecos)

class MimeEncoded(str):
	"indicates that this string is a MIME-encoded string"
	pass

class MimeDecoded(str):
	"indicates that this string is NOT a MIME-encoded string"
	pass

class AddressLine(object):
	"""
	EXAMPLES

	al = AddressLine((realname, email))  # realname is not MIME-encoded here

	al = AddressLine(email.utils.parseaddr("John Doe <john@example.net>"))  # not recommended

	al = AddressLine("John Doe <john@example.net>")  # recommended, the string is MIME-encoded here
	"""
	def __init__(self, p, eml=None):
		if isinstance(p, tuple):
			self.realname, self.email = p[:]
		else:
			realname_raw, self.email = email.utils.parseaddr(fix_unquoted_comma(p))
			if isinstance(p, MimeDecoded):
				self.realname = realname_raw
			else:
				self.realname = decode_mime_header(realname_raw, eml=eml)
		self.addressline = email.utils.formataddr((self.realname, self.email))
		# always put email address in angle brackets,
		# even if there is not realname part:
		if not self.addressline.endswith('>'):
			self.addressline = '<' + self.addressline + '>'
	def __str__(self):
		return self.addressline
	def __repr__(self):
		return repr(self.addressline)

def decode_mimetext(s):
	"""
	Takes one or more '=?...?=' tokens or non-encoded substrings and returns the complete decoded string.
	"""
	if s is not None:
		plain_str = ' '.join([s.decode(encoding or 'ascii', 'replace') for s, encoding in email.Header.decode_header(s)])
		return plain_str
	return s

def decode_mime_header(s, eml=None):
	"""
	Parameters
	
		eml: optional email object; if the charset can not be
		  detected, look up headers in this email to guess what would be
		  the correct charset before fall back to UTF-8
	"""
	chunks = []
	# unfold possibly folded header
	s = re.sub('\r?\n\s*', ' ', s)
	for chars, encoding in email.Header.decode_header(s):
		if encoding is None:
			# encoding is not specified in this header
			# first try to decode in UTF-8
			# then guess by other available encodings in the email
			# lastly fall back to UTF-8 but mask unrecognizable chars
			encodings = ['utf-8']
			if eml:
				for _x, part in walk_multipart(eml):
					m = re.search('\\bcharset=([a-z0-9_-]+)', part[HDR_CT] or '', re.I)
					if m:
						encodings.append(m.group(1))
			for encoding in encodings:
				try:
					chars.decode(encoding, 'strict')
					break
				except UnicodeDecodeError:
					encoding = None
			if encoding is None:
				encoding = 'utf-8'
		chunks.append(chars.decode(encoding, 'replace'))
	return ' '.join(chunks)

def walk_multipart(eml, leaf_only=False, depth=0):
	if not leaf_only:
		yield (depth, eml)
	if type(eml._payload) == list:
		for part in eml._payload:
			for x in walk_multipart(part, leaf_only, depth+1):
				yield x
	else:
		if leaf_only:
			yield (depth, eml)
