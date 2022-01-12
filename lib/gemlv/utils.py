#!/usr/bin/env python2

import re
import email
import pwd
import os

def fix_unquoted_comma(s):
	"""Many MUA do not enclose real names which contain comma, in quotation.
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
	return email.utils.getaddresses(map(fix_unquoted_comma, array))

def headercase(s):
	return re.sub(r'\b(.)', lambda x: x.group(1).upper(), s.lower())

def get_gecos_name():
	return re.sub(',.*,.*,.*', '', pwd.getpwuid(os.getuid()).pw_gecos)
