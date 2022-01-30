#!/usr/bin/env python2

from __future__ import absolute_import
import email
from gemlv.constants import *
import gemlv.profiler
from gemlv.contenttypestring import ContentTypeString
from gemlv.pythonutils import ItemIterator
import re
import gemlv.mime as mime
from gemlv.textutils import unquote_header_parameter


class PayloadTypeError(Exception):
	pass

class MimeCoded(str):
	def __init__(self, x):
		# None becomes '' here
		if x is None: x = ''
		super(str, self).__init__(x)

class MimeEncoded(MimeCoded):
	"indicates that this string is a MIME-encoded string"
	def __init__(self, x):
		if isinstance(x, MimeDecoded):
			raise TypeError
		super(self.__class__, self).__init__(x)

class MimeDecoded(MimeCoded):
	"indicates that this string is NOT a MIME-encoded string, but a user-consumable"
	def __init__(self, x):
		if isinstance(x, MimeEncoded):
			raise TypeError
		super(self.__class__, self).__init__(x)

class Header(object):
	def __init__(self, name, value=None, email=None):
		self.name = re.sub(r'\b(.)', lambda m: m.group(1).upper(), name.lower())
		self._hl_email = email  # the high level gemlv.Email object
		self._ll_email = self._hl_email._ll_email  # the low level email object
		self._value = HeaderValue(value, self)
		self.param = HeaderParameterAccessor(self)
		self.params = HeaderParameterPluralAccessor(self)
	
	@property
	def value(self):
		return self._value
	
	@value.setter
	def value(self, new):
		self._value = new
		self._value._header = self
	
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

class HeaderValue(object):
	def __init__(self, value, header_obj):
		assert isinstance(value, (MimeDecoded, MimeEncoded, None.__class__))
		
		self._encoded = None
		self._decoded = None
		self._header = header_obj
		self._hl_email = self._header._hl_email
		self._ll_email = self._hl_email._ll_email
		
		if isinstance(value, MimeEncoded):
			self._encoded = value
		else:
			self._decoded = value
	
	def _reinit(self):
		new_encoded_value = self._ll_email[self._header.name]
		if new_encoded_value is None: value = None
		else: value = MimeEncoded(new_encoded_value)
		self.__init__(value, self._header)
	
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
		self._set_header_value_on_email(old_encoded, self.encoded)
	
	@property
	def encoded(self):
		if self._encoded is None and self._decoded is not None:
			self._encoded = mime.encode_header(self._decoded, header_name=self._header.name, maxlinelen=email.Header.MAXLINELEN)
		return MimeEncoded(self._encoded)
	
	@encoded.setter
	def encoded(self, new):
		self._set_header_value_on_email(self._encoded, new)
		self._decoded = None
		self._encoded = new
	
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
		self._ll_email = self._hl_email._ll_email
	
	def __getitem__(self, pname):
		pvalue_uq = self._ll_email.get_param(pname, header=self._header.name, failobj='', unquote=False)
		pvalue = unquote_header_parameter(pvalue_uq)
		return HeaderValue(MimeEncoded(pvalue), self._header)
		# FIXME: if user calls .param[xy].decoded='...' then it changes the whole header value, not just the parameter's.
	
	def __setitem__(self, pname, pvalue):
		assert isinstance(pvalue, MimeEncoded)
		self._ll_email.set_param(pname, pvalue, header=self._header.name, requote=False)
		self._header.value._reinit()

class HeaderParameterPluralAccessor(object):
	def __init__(self, header_obj):
		self._header = header_obj
		self._hl_email = self._header._hl_email
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
			for pname, pval in \
			self._ll_email.get_params(header=self._header.name, failobj=[], unquote=False)\
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

class PluralHeaderAccessor(HeaderAccessor):
	def __getitem__(self, headername):
		return [Header(headername, MimeEncoded(encoded_value), self._hl_email) for encoded_value in self._ll_email.get_all(headername, [])]
	
	def __delitem__(self, headername):
		self._ll_email.__delitem__(headername)
	
	def __setitem__(self, headername, decoded_value):
		# TODO
		raise NotImplementedError
	
	def __contains__(self, headername):
		return self._ll_email.__contains__(headername)
	
	@property
	def keys(self):
		return self._ll_email.keys()
	
	def append(self, header_obj):
		assert isinstance(header_obj, Header)
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
	
	
	def as_string(self):
		return self._ll_email.as_string()
	
	def as_stream(self):
		from email.generator import Generator
		# TODO
		raise NotImplementedError
	
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
	
	@property
	def parts(self):
		"It's mainly for for-loop iteration."
		if self._ll_email.is_multipart():
			return MultipartPayload(self._ll_email._payload, self)
		else:
			return ()
	
	def set_payload(self, *args, **kwargs):
		self.size_approx = None
		return self._ll_email.set_payload(*args, **kwargs)
	
	def append_encoded_payload(self, encpayload):
		if self.is_multipart():
			raise PayloadTypeError('This is a MIME multipart message')
		self.size_approx = None
		self._ll_email._payload += encpayload
	
	def is_multipart(self):
		return self._ll_email.is_multipart()
	
	def get_charset(self):
		return self._ll_email.get_charset()
	
	def set_charset(self, *args, **kwargs):
		return self._ll_email.set_charset(*args, **kwargs)
	
	def get_content_charset(self):
		return self._ll_email.get_content_charset()
	
	@property
	def content_type(self):
		return ContentTypeString(self._ll_email.get_content_type())
	
	def get_filename(self):
		return self._ll_email.get_filename()
	
	def set_type(self, *args, **kwargs):
		return self._ll_email.set_type(*args, **kwargs)
	
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
			if self[HDR_CTE] == 'base64' or self[HDR_CTE] in ENCNAMES_UUE:
				# base64 and uuencoded have roughly 1/3 overhead
				return int(len(self._ll_email._payload) * 0.75)
			else:
				return len(self._ll_email.get_payload(decode=True))
	
	def attach(self, attachment):
		self.size_approx = None
		if not isinstance(attachment, self.__class__):
			attachment = self.__class__(attachment, self)
			# TODO: what if this attachment is attached to multiple envelopes at once
		self._ll_email.attach(attachment)
	
	def prepend_part(self, part):
		self.size_approx = None
		if not isinstance(part, self.__class__):
			part = self.__class__(part, self)
		self._ll_email._payload = [part] + self._ll_email._payload


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

