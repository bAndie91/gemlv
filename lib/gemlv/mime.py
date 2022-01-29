#!/usr/bin/env python

from __future__ import absolute_import
import email
import re

def decode_header(s, eml=None, unfold=True):
	"""
	Parameters
	
		eml: optional email object; if the charset can not be
		  detected, look up headers in this email to guess what would be
		  the correct charset before fall back to UTF-8
	"""
	chunks = []
	if unfold:
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
				for _depth, _index, part in walk_multipart(eml):
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
