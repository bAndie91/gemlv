#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import email
from gemlv.constants import *
import gemlv.profiler
from gemlv.contenttypestring import ContentTypeString
from gemlv.pythonutils import ItemIterator
import re
import gemlv.mime as mime
from gemlv.mimetext import MimeEncoded
from gemlv.mimetext import MimeDecoded
from gemlv.textutils import unquote_header_parameter
from gemlv.utils import decode_readably


class PayloadTypeError(Exception):
	pass


class Header(object):
	def __init__(self, name, value=None, email=None):
		self.raw_name = name
		# TODO: respect de-facto letter-case conventions, eg: DKIM-Signature, MIME-Version, Received-SPF, …
		self.name = re.sub(r'\b(.)', lambda m: m.group(1).upper(), self.raw_name.lower())
		self._hl_email = email  # the high level gemlv.Email object
		if self._hl_email:
			self._ll_email = self._hl_email._ll_email  # the low level email object
		self._value = HeaderValue(value, self)
		self.param = HeaderParameterAccessor(self)
		self.params = HeaderParameterPluralAccessor(self)
	
	@property
	def nonempty(self):
		return bool(self.value.decoded)
	
	@property
	def value(self):
		return self._value
	
	@value.setter
	def value(self, new):
		self._value = new
		self._value._header = self
	
	# shortcut methods:
	
	@property
	def decoded(self):
		return self.value.decoded
	
	@decoded.setter
	def decoded(self, new):
		self.value.decoded = new
	
	@property
	def encoded(self):
		return self.value.encoded
	
	@encoded.setter
	def encoded(self, new):
		self.value.encoded = new

class MimeTextValue(object):
	"""
	MimeTextValue represents arbitrary string both in user-consumable form and in MIME-encoded form.
	When value is set by either .encoded or .decoded attribute, it calls update_func(old_value, new_value)
	to let the new encoded value known by other parts of the code.
	You may set update_func to a method which updates an email's headers.
	
	Attributes
	
		decoded
		
		returns the decoded, user-consumable string.
		if a "=?..." sequence in the encoded form can not be decoded, returns it as-is.
		
		encoded
		
		returns the raw string, MIME-encoded if needed (ie. starting with "=?").
	"""
	
	def __init__(self, value, header_obj, update_func):
		assert isinstance(value, (MimeDecoded, MimeEncoded, basestring, None.__class__))
		self._encoded = None
		self._decoded = None
		self._header = header_obj
		self._hl_email = self._header._hl_email
		if self._hl_email:
			self._ll_email = self._hl_email._ll_email
		# update_func is called when the value is to be changed and
		# its responsibility to propagate changes up to the low level email object
		self._update_func = update_func
		
		if isinstance(value, MimeEncoded):
			self._encoded = value
		elif isinstance(value, MimeDecoded):
			self._decoded = value
		else:
			# detect encoding
			try:
				self._encoded = MimeEncoded(value)
			except UnicodeDecodeError:
				encodings = []
				email_charset = self._ll_email.get_param('charset', header=HDR_CT)
				if email_charset:
					encodings.append(email_charset)
				encodings.extend(os.environ.get('FALLBACK_ENCODINGS', 'utf-8').split(':'))
				for encoding in encodings:
					try:
						value.decode(encoding, 'strict')
						break
					except UnicodeDecodeError:
						encoding = None
				if encoding is None:
					raise
				self._decoded = MimeDecoded(value.decode(encoding))
	
	@property
	def decoded(self):
		if self._decoded is None and self._encoded is not None:
			self._decoded = mime.decode_header(self._encoded, eml=self._hl_email, unfold=True)
		return MimeDecoded(self._decoded)
	
	@decoded.setter
	def decoded(self, new):
		old_encoded = self.encoded
		self._decoded = new
		self._encoded = None
		self._update_func(old_encoded, self.encoded)
	
	@property
	def encoded(self):
		if self._encoded is None and self._decoded is not None:
			self._encoded = mime.encode_header(self._decoded, header_name=self._header.name, maxlinelen=email.Header.MAXLINELEN)
		return MimeEncoded(self._encoded)
	
	@encoded.setter
	def encoded(self, new):
		self._update_func(self._encoded, MimeEncoded(new))
		self._decoded = None
		self._encoded = new

class HeaderValue(MimeTextValue):
	def __init__(self, value, header_obj):
		super(self.__class__, self).__init__(value, header_obj, self._update_func)
	
	def _update_func(self, old, new):
		assert isinstance(new, MimeEncoded)
		self._set_header_value_on_email(old, new)
	
	def _set_header_value_on_email(self, old, new):
		if self._ll_email.__contains__(self._header.name):
			# if there are multiple headers with the same name, replce that one
			# which this HeaderValue represents
			for index, header_tuple in enumerate(self._ll_email._headers):
				hname, hval = header_tuple
				if hname.lower() == self._header.name.lower() and hval == old:
					self._ll_email._headers[index] = (hname, new)
					break
			else:
				raise ValueError('no such email header')
		else:
			# there was not a header with this name so far, so add it now
			self._ll_email.add_header(self._header.name, new)

class HeaderParameterAccessor(object):
	def __init__(self, header_obj):
		self._header = header_obj
		self._hl_email = self._header._hl_email
		if self._hl_email:
			self._ll_email = self._hl_email._ll_email
	
	def __getitem__(self, pname):
		pvalue_possible_quoted = self._ll_email.get_param(pname, header=self._header.name, failobj='', unquote=False)
		if isinstance(pvalue_possible_quoted, tuple):
			# it sometimes retuns with a tuple like ('UTF-8', '', 'the actual content') instead of a string.
			# for example this header parameter:
			#   filename*0*=UTF-8''%74%68%65%20%61%63%74%75%61%6c%20%63%6f%6e%74%65%6e%74
			pvalue_possible_quoted = pvalue_possible_quoted[2].decode(pvalue_possible_quoted[0])
			pvalue = unquote_header_parameter(pvalue_possible_quoted)
			return HeaderParameterValue(pname, MimeDecoded(pvalue), self._header)
		pvalue = unquote_header_parameter(pvalue_possible_quoted)
		# the following try-except detects if the header parameter value is already decoded (in say UTF-8),
		# or is it in MIME-encoded form - which it normally should be.
		try:
			# unicode() fails if there is non-ascii char in pvalue which is supposed to be ascii-only normally.
			unicode(pvalue)
		except UnicodeDecodeError:
			# if it is indeed non-ascii-only, try to string-decode (not MIME-decode because it is probably not in MIME-encoded status) it
			# from the guessed character encoding (decode_readably() guesses the most likely charset).
			pvalue_guessed_coding_status = MimeDecoded(decode_readably(pvalue, self._hl_email))
		else:
			# if it is ascii-only, take it as a MIME-encoded data.
			pvalue_guessed_coding_status = MimeEncoded(pvalue)
		return HeaderParameterValue(pname, pvalue_guessed_coding_status, self._header)

class HeaderParameterPluralAccessor(object):
	def __init__(self, header_obj):
		self._header = header_obj
		self._hl_email = self._header._hl_email
		if self._hl_email:
			self._ll_email = self._hl_email._ll_email
	
	@property
	def decoded(self):
		return [\
			(\
				MimeDecoded(mime.decode_header(pname, eml=self._hl_email, unfold=True)), \
				MimeDecoded(mime.decode_header(pval, eml=self._hl_email, unfold=True)) \
			)\
			for pname, pval in self.encoded \
		]
	
	@decoded.setter
	def decoded(self, decoded_list_of_tuples):
		self._header.value.encoded = ''
		for n, v in decoded_list_of_tuples:
			en = mime.encode_header(n)
			ev = mime.encode_header(v)
			self._header.param[en].encoded = MimeEncoded(ev)
	
	@property
	def encoded(self):
		return [(MimeEncoded(pname), MimeEncoded(unquote_header_parameter(pval))) \
			for pname, pval in self.items
		]
	
	@encoded.setter
	def encoded(self, encoded_list_of_tuples):
		self._header.value.encoded = ''
		for n, v in encoded_list_of_tuples:
			self._header.param[n].encoded = MimeEncoded(v)
	
	@property
	def keys(self):
		return dict(self.encoded).keys()
	
	def __contains__(self, pname):
		parameter_names = [p.lower() for p in self.keys()]
		return pname.lower() in parameter_names
	
	@property
	def items(self):
		# borrowed from email.message._get_params_preserve
		_parseparam = email.message._parseparam
		params = []
		for p in _parseparam(';' + self._header.value.encoded):
			try:
				name, val = p.split('=', 1)
				name = name.strip()
				val = val.strip()
			except ValueError:
				# Must have been a bare attribute
				name = p.strip()
				val = ''
			if name:
				# TODO: are param names case insensitive?
				# name = name.lower()
				# unquote the value here, because email.utils.unquote does it wrong,
				val = unquote_header_parameter(val)
				# however if the unquoted value also enclosed in double-quotes or angle brackets,
				# it will be stripped again.
				if (val.startswith('"') and val.endswith('"')) or (val.startswith('<') and val.endswith('>')):
					# it's safe to MIME-encode it in utf-8 because it is most likely ascii text, otherwise it
					# would be starting with "=?" sequence.
					val = email.Header.make_header([(val, 'utf-8')])
				params.append((name, val))
		if params:
			# it handles RFC 2231 headers for us
			params = email.utils.decode_params(params)
			# but quotes all parameter values (despite nobody asked) except the 1st one
			# so reverse it:
			for index, (name, value_quoted) in enumerate(params):
				if index == 0: continue
				params[index] = (name, unquote_header_parameter(value_quoted))
		return params

class HeaderParameterValue(MimeTextValue):
	def __init__(self, param_name, param_value, header_obj):
		super(self.__class__, self).__init__(param_value, header_obj, self._update_func)
		self.name = param_name.lower()
	
	def _update_func(self, _old, new):
		assert isinstance(new, MimeEncoded)
		self._set_parameter_value_in_header_value(new)
	
	def _set_parameter_value_in_header_value(self, new):
		param_separator = email.message.SEMISPACE
		_formatparam = email.message._formatparam
		requote = False
		
		new_params = []
		this_param_found = False
		for pn, pv in self._header.params.items:
			if pn.lower() == self.name:
				pv = new
				this_param_found = True
			new_params.append(_formatparam(pn, pv, requote))
		if not this_param_found:
			new_params.append(_formatparam(self.name, new, requote))
		self._header.value.encoded = param_separator.join(new_params)


class HeaderAccessor(object):
	def __init__(self, email_obj):
		self._hl_email = email_obj
		self._ll_email = self._hl_email._ll_email

class SingularHeaderAccessor(HeaderAccessor):
	def __getitem__(self, headername):
		encoded_value = self._ll_email.get(headername, '')
		return Header(headername, encoded_value, self._hl_email)
	
	def __setitem__(self, headername, value):
		assert isinstance(value, HeaderValue)
		self._ll_email.__delitem__(headername)
		self[headername].value = value

class HeaderList(list):
	def __init__(self, init):
		super(self.__class__, self).__init__(init)
	
	@property
	def encoded(self):
		return [header.encoded for header in self]
	
	@encoded.setter
	def encoded(self, new):
		raise NotImplementedError
	
	@property
	def decoded(self):
		return [header.decoded for header in self]
	
	@decoded.setter
	def decoded(self, new):
		raise NotImplementedError

class PluralHeaderAccessor(HeaderAccessor):
	"access multiple headers with the same name (eg. Received)"
	def __getitem__(self, headername):
		return HeaderList([Header(headername, encoded_value, self._hl_email) \
			for encoded_value in self._ll_email.get_all(headername, [])])
	
	def __setitem__(self, headername, decoded_value):
		raise NotImplementedError
	
	def __delitem__(self, headername):
		self._ll_email.__delitem__(headername)
	
	def __contains__(self, headername):
		return self._ll_email.__contains__(headername)
	
	@property
	def keys(self):
		return [Header(name).name for name in self._ll_email.keys()]
	
	@property
	def items(self):
		return [Header(name, value, self._hl_email) for name, value in self._ll_email._headers]
	
	def append(self, header_obj):
		assert isinstance(header_obj, Header)
		# Note, we don't carry on the header_obj's connection to its original Email (header_obj._hl_email)
		# to let it freed. This may lead to exception in mime.decode_header or garbage chars in the
		# decoded representation, if there was bad or missing charset or invalid byte-sequence in the 
		# original MIME-encoded value.
		self._ll_email.add_header(header_obj.name, header_obj.value.encoded)


def _set_header(mimepart, hname, hvalue):
	try:
		mimepart.replace_header(hname, hvalue)
	except KeyError as e:
		mimepart.add_header(hname, hvalue)

def _fix_parts_by_cte(mime_part):
	# fix defect in email module (version 4.0.3 but others are likely affected too)
	# that it does not obey Content-Transfer-Encoding when decoding multipart MIME objects.
	
	if mime_part.is_multipart():
		cte = mime_part.get(HDR_CTE, '').lower()
		if cte in ('quoted-printable', 'base64') + ENCNAMES_UUE:
			# create a temporarly email object to reuse email module's decoding routines
			aux_email = email.message.Message()
			# manually split the input email object (potentially multipart MIME attachment) into headers and raw body
			raw_mime_part = mime_part.as_string()
			mimepart_headers, aux_email._payload = re.split(r'\r?\n\r?\n', raw_mime_part, 1)
			# copy the input email object's CTE to the temporarly email
			_set_header(aux_email, HDR_CTE, cte)
			# let the upstream email module decode it as a non-multipart MIME payload
			payload_decoded = aux_email.get_payload(decode=True)
			# construct a new MIMEMessage from the original (input) email headers and its properly decoded payload (except the CTE it not what was originally)
			mimepart_decoded = email.message_from_string(mimepart_headers + '\r\n\r\n' + payload_decoded)
			# replace the input email's sub-MIME-parts to those which are just yielded
			mime_part.set_payload([])
			_set_header(mime_part, HDR_CTE, '8bit')
			mime_part.set_payload(mimepart_decoded.get_payload())
		elif cte in ('', '7bit', '8bit'):
			pass
		else:
			raise Exception("don't know how to decode %s Content-Transfer-Encoding" % (cte,))
		
		#for subpart in mime_part....

class Email(object):
	def __init__(self, email_obj, parent_email_obj=None):
		if isinstance(email_obj, self.__class__):
			email_obj = email_obj._ll_email
		self._ll_email = email_obj  # the low level email object
		self.parent = parent_email_obj
		self._size_approx = None
		_fix_parts_by_cte(email_obj)
	
	@property
	def header(self):
		return SingularHeaderAccessor(self)
	
	@property
	def headers(self):
		return PluralHeaderAccessor(self)
	
	def as_stream(self):
		from email.generator import Generator
		# TODO
		raise NotImplementedError
	
	@property
	def content_type(self):
		return ContentTypeString(self._ll_email.get_content_type())
	
	@content_type.setter
	def content_type(self, content_type):
		self._ll_email.set_type(content_type, requote=False)
	
	@property
	def filename(self):
		return self.header[HDR_CD].param['filename'].decoded \
			or self.header[HDR_CT].param['name'].decoded
	
	@property
	def parts(self):
		if self._ll_email.is_multipart():
			return MultipartPayload(self)
		else:
			return ()
	
	@property
	def body_encoded(self):
		raw = self._ll_email.as_string()
		header, body = re.split(r'\r?\n\r?\n', raw, 1)
		return body
	
	@property
	def payload_encoded(self):
		if self._ll_email.is_multipart():
			return self.body_encoded
		else:
			return self._ll_email.get_payload(decode=False)
	
	@payload_encoded.setter
	def payload_encoded(self, encpayload):
		self.size_approx = None
		self._ll_email.set_payload(encpayload)
	
	@property
	def payload_decoded(self):
		if self._ll_email.is_multipart():
			raise PayloadTypeError('This is a MIME multipart message')
		return self._ll_email.get_payload(decode=True)
	
	def append_encoded_payload(self, encpayload):
		if self.is_multipart():
			raise PayloadTypeError('This is a MIME multipart message')
		self.size_approx = None
		self._ll_email._payload += encpayload
	
	@property
	def size_approx(self):
		if self._size_approx is None:
			size_approx = 0
			if self.is_multipart():
				for part in self.parts:
					size_approx += part.size_approx
			else:
				size_approx = len(self._ll_email._payload)
			# TODO count size of headers
			self._size_approx = size_approx
		return self._size_approx
	
	@size_approx.setter
	def size_approx(self, size):
		if size is None and self.parent is not None:
			# clear the parent email object's size to have it re-calculated when queried
			self.parent.size_approx = None
		self._size_approx = size
	
	@property
	def size_decoded_approx(self):
		if self.is_multipart():
			return self.size_approx
		else:
			if self._ll_email[HDR_CTE] == 'base64' or self._ll_email[HDR_CTE] in ENCNAMES_UUE:
				# base64 and uuencoded have roughly 1/3 overhead
				return int(len(self._ll_email._payload) * 0.75)
			else:
				return len(self._ll_email.get_payload(decode=True))
	
	def prepend_part(self, part):
		self.size_approx = None
		if isinstance(part, self.__class__): part = part._ll_email
		self._ll_email._payload.insert(0, [part])
	
	def iterate_parts_recursively(self, leaf_only=False, depth=0, index=0):
		if not leaf_only or not self.is_multipart():
			yield (depth, index, self)
		subindex = 0
		for part in self.parts:
			# replace it with "yield from":
			for x in part.iterate_parts_recursively(leaf_only, depth+1, subindex):
				yield x
			subindex += 1
	
	# proxy methods:
	
	def as_string(self):
		return self._ll_email.as_string()
	
	def get_charset(self):
		return self._ll_email.get_charset()
	
	def set_charset(self, *args, **kwargs):
		self._ll_email.set_charset(*args, **kwargs)
	
	
	def is_multipart(self):
		return self._ll_email.is_multipart()
	
	@property
	def preamble(self):
		s = self._ll_email.preamble
		if s is None: return ''
		return s
	
	@preamble.setter
	def preamble(self, s):
		self._ll_email.preamble = s
	
	@property
	def epilogue(self):
		s = self._ll_email.epilogue
		if s is None: return ''
		return s
	
	@epilogue.setter
	def epilogue(self, s):
		self._ll_email.epilogue = s
	
	def attach(self, item):
		self.size_approx = None
		# add te low-level email object to the attachments
		if isinstance(item, self.__class__): item = item._ll_email
		self._ll_email.attach(item)
	
	
	# the following proxy methods are not meant to be used by the user,
	# but kept for internal use by low-level code (email.generator.Generator).
	
	def get_payload(self, *args, **kwargs):
		return self._ll_email.get_payload(*args, **kwargs)


class MultipartPayload(object):
	"""
	this class represents email payload and maintains the parent email object's 
	registered size when changing payloads in place
	"""
	
	def __init__(self, email_obj):
		self._hl_email = email_obj
	
	def __setitem__(self, itemname, item):
		self._hl_email.size_approx = None
		# set the low-level email object
		if isinstance(item, self._hl_email.__class__): item = item._ll_email
		self._hl_email._ll_email._payload.__setitem__(itemname, item)
	
	def __delitem__(self, itemname):
		self._hl_email.size_approx = None
		self._hl_email._ll_email._payload.__delitem__(itemname)
	
	def __getitem__(self, itemname):
		item = self._hl_email._ll_email._payload.__getitem__(itemname)
		# make it look like a high-level Email object
		return self._hl_email.__class__(item, self._hl_email)
	
	def __getslice__(self, start, end):
		return [self._hl_email.__class__(item, self._hl_email) for item in \
			self._hl_email._ll_email._payload.__getslice__(start, end)]
	
	def __delslice__(self, *_p):
		raise NotImplementedError
	
	def __setslice__(self, *_p):
		raise NotImplementedError
	
	def __len__(self):
		return self._hl_email._ll_email._payload.__len__()
	
	def __iter__(self):
		return ItemIterator(self)
	
	def index(self, item):
		# search for the low-level email object in the payloads
		if isinstance(item, self._hl_email.__class__): item = item._ll_email
		return self._hl_email._ll_email._payload.index(item)
	
	def remove(self, item):
		self._hl_email.size_approx = None
		# search for the low-level email object in the payloads
		if isinstance(item, self._hl_email.__class__): item = item._ll_email
		self._hl_email._ll_email._payload.remove(item)
	
	def clear(self):
		self._hl_email.size_approx = None
		self._hl_email._ll_email._payload = []
	
	def pop(self, *args):
		self._hl_email.size_approx = None
		return self._hl_email._ll_email._payload.pop(*args)
	
	def insert(self, index, item):
		self._hl_email.size_approx = None
		# add the low-level email object into the payloads
		if isinstance(item, self._hl_email.__class__): item = item._ll_email
		return self._hl_email._ll_email._payload.insert(index, item)

