#!/usr/bin/env python2

from __future__ import absolute_import
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


class PayloadTypeError(Exception):
	pass


class Header(object):
	def __init__(self, name, value=None, email=None):
		self.name = re.sub(r'\b(.)', lambda m: m.group(1).upper(), name.lower())
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
		
		returns the raw string, MIME-encoded if needed (ie. start with "=?").
	"""
	
	def __init__(self, value, header_obj, update_func):
		assert isinstance(value, (MimeDecoded, MimeEncoded, None.__class__))
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
		else:
			self._decoded = value
	
	@property
	def decoded(self):
		if self._decoded is None and self._encoded is not None:
			self._decoded = mime.decode_header(self._encoded, eml=self._hl_email, unfold=False)
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
		pvalue_uq = self._ll_email.get_param(pname, header=self._header.name, failobj='', unquote=False)
		pvalue = unquote_header_parameter(pvalue_uq)
		return HeaderParameterValue(pname, MimeEncoded(pvalue), self._header)

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
				MimeDecoded(mime.decode_header(pname, eml=self._hl_email, unfold=False)), \
				MimeDecoded(mime.decode_header(pval, eml=self._hl_email, unfold=False)) \
			)\
			for pname, pval in self.encoded \
		]
	
	@decoded.setter
	def decoded(self, decoded_list_of_tuples):
		self._header.value.encoded = ''
		for n, v in decoded_list_of_tuples:
			en = mime.encode_header(n)
			ev = mime.encode_header(v)
			self._header.param[en] = MimeEncoded(ev)
	
	@property
	def encoded(self):
		return [(MimeEncoded(pname), MimeEncoded(unquote_header_parameter(pval))) \
			for pname, pval in self.items
		]
	
	@encoded.setter
	def encoded(self, encoded_list_of_tuples):
		self._header.value.encoded = ''
		for n, v in encoded_list_of_tuples:
			self._header.param[n] = MimeEncoded(v)
	
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
			# TODO: are param names case insensitive?
			params.append((name, unquote_header_parameter(val)))
		params = email.utils.decode_params(params)
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
		return Header(headername, MimeEncoded(encoded_value), self._hl_email)
	
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
	def __getitem__(self, headername):
		return HeaderList([Header(headername, MimeEncoded(encoded_value), self._hl_email) \
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
		return [Header(name, MimeEncoded(value), self._hl_email) for name, value in self._ll_email._headers]
	
	def append(self, header_obj):
		assert isinstance(header_obj, Header)
		# Note, we don't carry on the header_obj's connection to its original Email (header_obj._hl_email)
		# to let it freed. This may lead to exception in mime.decode_header or garbage chars in the
		# decoded representation, if there was bad or missing charset or invalid byte-sequence in the 
		# original MIME-encoded value.
		self._ll_email.add_header(header_obj.name, header_obj.value.encoded)


class Email(object):
	def __init__(self, email_obj, parent_email_obj = None):
		if isinstance(email_obj, self.__class__):
			email_obj = email_obj._ll_email
		self._ll_email = email_obj  # the low level email object
		self.parent = parent_email_obj
		self.origin_path = None
		self._size_approx = None
	
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
	def parts(self):
		"It's mainly for for-loop iteration."
		if self._ll_email.is_multipart():
			return MultipartPayload(self._ll_email._payload, self)
		else:
			return ()
	
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
		if not isinstance(part, self.__class__):
			part = self.__class__(part, self)
		self._ll_email._payload = [part] + self._ll_email._payload
	
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
	
	
	@property
	def _payload(self):
		if self._ll_email.is_multipart():
			return MultipartPayload(self._ll_email._payload, self)
		else:
			return self._ll_email._payload
	
	def get_payload(self, *args, **kwargs):
		payload = self._ll_email.get_payload(*args, **kwargs)
		if isinstance(payload, list):
			return MultipartPayload(payload, self)
		else:
			return payload
	
	def set_payload(self, *args, **kwargs):
		self.size_approx = None
		return self._ll_email.set_payload(*args, **kwargs)
	
	
	def is_multipart(self):
		return self._ll_email.is_multipart()
	
	@property
	def preamble(self):
		return self._ll_email.preamble
	
	@preamble.setter
	def preamble(self, s):
		self._ll_email.preamble = s
	
	@property
	def epilogue(self):
		return self._ll_email.epilogue
	
	@epilogue.setter
	def epilogue(self, s):
		self._ll_email.epilogue = s
	
	def attach(self, attachment):
		self.size_approx = None
		if not isinstance(attachment, self.__class__):
			attachment = self.__class__(attachment, self)
			# TODO: what if this attachment is attached to multiple envelopes at once
		self._ll_email.attach(attachment)
	
	
	# the following proxy methods are not meant to be used by the user,
	# but kept for internal use by low-level code (email.generator.Generator).
	
	def get_charset(self):
		return self._ll_email.get_charset()
	
	def get_unixfrom(self):
		return self._ll_email.get_unixfrom()
	
	def get_content_charset(self):
		return self._ll_email.get_content_charset()
	
	def get_content_maintype(self):
		return self._ll_email.get_content_maintype()
	
	def get_content_subtype(self):
		return self._ll_email.get_content_subtype()
	
	def get_filename(self):
		return self._ll_email.get_filename()
	
	def get_boundary(self, *args, **kwargs):
		return self._ll_email.get_boundary(*args, **kwargs)

	def set_boundary(self, *args, **kwargs):
		self._ll_email.set_boundary(*args, **kwargs)
	
	def items(self, *args, **kwargs):
		return self._ll_email.items(*args, **kwargs)

	def walk(self, *args, **kwargs):
		return self._ll_email.walk(*args, **kwargs)


class MultipartPayload(list):
	"this class represents email payload and maintains the parent email object's registered size when changing payloads in place"
	
	def __init__(self, payload_obj, email_obj):
		super(self.__class__, self).__init__(payload_obj)
		self._payload_obj = payload_obj
		self._hl_email = email_obj
		# let type checking done by the called methods, not us
	
	def __setitem__(self, itemname, item):
		self._hl_email.size_approx = None
		return self._payload_obj.__setitem__(itemname, item)
	
	def __delitem__(self, itemname):
		self._hl_email.size_approx = None
		return self._payload_obj.__delitem__(itemname)
	
	def __getitem__(self, itemname):
		item = self._payload_obj.__getitem__(itemname)
		# if any MIME part happens not to be also a gemlv.email.Email object,
		# then wrap it around and replace. it may happen when loading the email
		# object by eg. email.message_from_file or email.message_from_string.
		if not isinstance(item, self._hl_email.__class__):
			item = self._hl_email.__class__(item)
			self._payload_obj.__setitem__(itemname, item)
		return item
	
	def __getslice__(self, *_p):
		raise NotImplementedError
	
	def __delslice__(self, *_p):
		raise NotImplementedError
	
	def __setslice__(self, *_p):
		raise NotImplementedError
	
	def __iter__(self):
		return ItemIterator(self)
	
	def remove(self, item):
		self._hl_email.size_approx = None
		return self._payload_obj.remove(item)
	
	def pop(self, *p):
		self._hl_email.size_approx = None
		return self._payload_obj.pop(*p)
	
	def insert(self, index, item):
		self._hl_email.size_approx = None
		return self._payload_obj.insert(index, item)

