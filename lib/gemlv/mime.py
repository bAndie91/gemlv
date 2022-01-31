#!/usr/bin/env python

from __future__ import absolute_import
import email
import re
from gemlv.textutils import unquote_header_parameter
from gemlv.constants import *


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
	# it does not decodes MIME-encoded strings which immediately followed by semicolon
	# TODO: decode first no-value parameter too?
	for chars, encoding in email.Header.decode_header(s):
		if encoding is None:
			# encoding is not specified in this header
			# first try to decode in UTF-8
			# then guess by other available encodings in the email
			# lastly fall back to UTF-8 but mask unrecognizable chars
			encodings = ['utf-8']
			if eml:
				for _depth, _index, part in eml.iterate_parts_recursively():
					# do not call .decoded here because it will call us thus infinite recursion; 
					# and hope charset is not really MIME-encoded away
					charset = part.header[HDR_CT].param['charset'].encoded
					if charset: encodings.append(charset)
					# TODO: search charset definitions in MIME-encoded texts in each individual header
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

def encode_header(header_value, **make_header_params):
	# TODO: obey maxlinelen
	"""
	Make an RFC 2047-compilant header value string (without line breaks),
	ie. encode non-ascii-only words, but leave ascii-only words as-is.
	Encode subsequent non-ascii-only words together to keep space chars.
	
	Parameters
	
		header_value: string, mandatory
		header_name: string, optional, default: None
		maxlinelen: int, optional, default: None
		continuation_ws: string, optional, default: a space
	"""
	chunks = []
	CHUNK_PLAIN, CHUNK_ENCODED = range(2)
	separator = ' '
	prev_word = None
	prev_chunk = None
	for word in header_value.split(separator):
		try:
			if prev_chunk is not None and word == '':
				# two or more spaces follow a non-ascii-only word, this might result
				# in two subsequent MIME-encoded words (two or more spaces between them)
				# which is in turn decoded as one continuous word instead of two.
				# ie. whitespace between MIME-encoded words are ignored.
				# so jump to the CHUNK_ENCODED branch to snap the extra space to the
				# word before it.
				raise UnicodeError()
			chunk = email.Header.make_header([(word, None)], **make_header_params)
			chunk_type = CHUNK_PLAIN
		except (UnicodeDecodeError, UnicodeError):
			if prev_word is not None:
				word = prev_word + separator + word
			chunk = email.Header.make_header([(word, 'UTF-8')], **make_header_params)
			chunk_type = CHUNK_ENCODED
		chunk = chunk.encode()
		if chunk_type == CHUNK_PLAIN:
			if prev_chunk is not None:
				chunks.append(prev_chunk)
			chunks.append(chunk)
			prev_word = None
			prev_chunk = None
		else:
			prev_word = word
			prev_chunk = chunk
	if prev_chunk is not None:
		chunks.append(prev_chunk)
	return separator.join(chunks)
