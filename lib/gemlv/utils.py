#!/usr/bin/env python2

from __future__ import absolute_import
import email.utils
import re
import pwd
import os
from gemlv.constants import *
from gemlv.sysutils import warnx
from gemlv.mimetext import MimeDecoded
from gemlv.mimetext import MimeEncoded
import gemlv.mime as mime


def fix_unquoted_comma(s):
	"""Many MUA do not enclose real names which contain comma in double quotes.
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

def _getaddresses(array):
	return filter(lambda a: a[1] != '', email.utils.getaddresses(map(fix_unquoted_comma, array)))

def getaddresslines(array):
	"""
	Arguments
	
		array: list of MIME-decoded strings
	"""
	return map(lambda t: AddressLine(t), _getaddresses(array))

def get_gecos_name():
	return re.sub(',.*,.*,.*', '', pwd.getpwuid(os.getuid()).pw_gecos)

class AddressLine(object):
	"""
	EXAMPLES

	al = AddressLine((realname, email))  # realname is NOT MIME-encoded here

	al = AddressLine(email.utils.parseaddr("John Doe <john@example.net>"))  # not recommended

	al = AddressLine("John Doe <john@example.net>")  # recommended, the string has to be MIME-encoded here
	"""
	def __init__(self, p, eml=None):
		assert isinstance(p, (tuple, MimeEncoded, MimeDecoded))
		if isinstance(p, tuple):
			self.realname, self.email = p[:]
		else:
			realname_raw, self.email = email.utils.parseaddr(fix_unquoted_comma(p))
			if isinstance(p, MimeDecoded):
				self.realname = realname_raw
			else:
				self.realname = mime.decode_header(realname_raw, eml=eml)
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
