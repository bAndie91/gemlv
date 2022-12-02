#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

def list2text(l):
	return ''.join(map(lambda x: x+'\n', l))

def human_size(x, suffix='B', decimals=1):
	prefixa = ['', 'K', 'M', 'G']
	for prefixum in prefixa:
		if abs(x) < 1024.0 or prefixum == prefixa[-1]:
			return '%.*f %s%s' % (decimals, x, prefixum, suffix)
		x /= 1024.0

# email.utils.unquote() doesn't properly de-backslash-ify in email module 4.0.3
def unquote_header_parameter(s):
    """Remove quotes from a string."""
    if len(s) > 1:
        if s.startswith('"') and s.endswith('"'):
        	return re.sub(r'\\([\\"])', lambda m: m.group(1), s[1:-1])
        if s.startswith('<') and s.endswith('>'):
            return s[1:-1]
    return s

def shorturl(url, maxlength=72):
	if len(url) > maxlength:
		return url[0:maxlength-1] + '…'
	else:
		return None

def wildcardmatch(subject, pattern):
	from fnmatch import fnmatch
	return fnmatch(subject.lower(), pattern.lower())

def truish(x):
	return(str(x).lower() in ['yes', '1', 'true', 'on'])

def noaccent(s):
	# from unidecode import unidecode; return unidecode(s)
	import unicodedata
	# Nonspacing_Mark = 'Mn'
	# ... if unicodedata.category(c) != Nonspacing_Mark
	return ''.join([c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)])
