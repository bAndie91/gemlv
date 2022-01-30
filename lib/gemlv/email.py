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

class MimeEncoded(str):
	"indicates that this string is a MIME-encoded string"
	pass

class MimeDecoded(str):
	"indicates that this string is NOT a MIME-encoded string, but a user-consumable"
	pass

class Header(object):
	def __init__(self, name, value=None, eml=None):
		self.name = re.sub(r'\b(.)', lambda m: m.group(1).upper(), name.lower())
		self._eml = eml
		self.value = HeaderValue(value, header=self)
		self.param = HeaderParameterAccessor(header=self)

class HeaderValue(object):
	def __init__(self, value, header_obj)
		assert isinstance(value, (MimeDecoded, MimeEncoded, None.__class__))
		
		self._encoded = None
		self._decoded = None
		self._header = header_obj
		
		if isinstance(value, MimeEncoded):
			self._encoded = value
		else:
			self._decoded = value
	
	def _reinit(self):
		header = self._header
		new_encoded_value = header._eml[header.name]
		if new_encoded_value is None: value = None
		else: value = MimeEncoded(new_encoded_value)
		self.__init__(value, header)
	
	@property
	def decoded(self):
		if self._decoded is None:
			if self._encoded is None:
				return ''
			self._decoded = mime.decode_header(self._encoded, eml=self._header._eml, unfold=False)
		return self._decoded
	
	@property
	def encoded(self):
		if self._encoded is None:
			if self._decoded is None:
				return ''
			self._encoded = mime.encode_header(self._decoded, header_name=self._header.name, maxlinelen=email.Header.MAXLINELEN)
		return self._encoded
	
	@decoded.setter
	def decoded(self, new):
		# TODO
		raise NotImplementedError()
	
	@encoded.setter
	def encoded(self, new):
		# TODO
		raise NotImplementedError()

class HeaderParameterAccessor(object):
	RE_HEADERPARAM = r'\b(%s)\b(=(?:\x22([^\x22]+)\x22|([^\s;]+)))?'
	
	def __init__(self, header_obj):
		self._header = header_obj
	
	def __getitem__(self, pname):
		pvalue = ''
		matches = re.findall(self.RE_HEADERPARAM % (re.escape(pname),), self._header.value.encoded, re.I)
		if matches:
			left, right, doublequoted_val, unquoted_val = matches[-1]
			if doublequoted_val != '': pvalue = doublequoted_val
			elif unquoted_val != '': pvalue = unquoted_val
		return HeaderValue(MimeEncoded(pvalue), self._header)
	
	def __setitem__(self, pname, pvalue):
		assert isinstance(pvalue, MimeEncoded)
		self._header._eml.set_param(pname, pvalue, header=self._header.name, requote=False)
		self._header.value._reinit()
	
	def all(self):
		header = self._header
		return [(pname, MimeEncoded(unquote_header_parameter(pval)) for pname, pval in header._eml.get_params(header=header.name, failobj=[], unquote=False)]
	
	def __contains__(self, pname):
		parameter_names = [p.lower() for p in dict(self.all).keys()]
		return pname.lower() in parameter_names

class HeaderAccessor(object):
	def __init__(self, email_obj):
		self.email = email_obj

class SingularHeaderAccessor(HeaderAccessor):
	def __getitem__(self, headername):
		encoded_value = self.email.get(headername, '')
		return Header(headername, MimeEncoded(encoded_value), self.email)
	
	def __setitem__(self, headername, decoded_value):
		# TODO
		raise NotImplementedError()

class PluralHeaderAccessor(HeaderAccessor):
	def __getitem__(self, headername):
		return [Header(headername, MimeEncoded(encoded_value), self.email) for encoded_value in self.email.get_all(headername, [])]
	
	def __delitem__(self, headername):
		self.email.__delitem__(headername)
	
	def __setitem__(self, headername, decoded_value):
		# TODO
		raise NotImplementedError()
	
	def __contains__(self, headername):
		return self.email.__contains__(headername)
	
	def append(self, header_obj):
		self.email.add_header(header_obj.name, header_obj.value.encoded)

class Email(object):
	def __init__(self, email_obj, parent_email_obj = None):
		self.email = email_obj
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
		return self.email.as_string()
	
	def as_stream(self):
		from email.generator import Generator
		# TODO
		raise NotImplementedError()
	
	@property
	def _payload(self):
		if self.email.is_multipart():
			return MultipartPayload(self.email._payload, self)
		else:
			return self.email._payload
	
	def get_payload(self, *args, **kwargs):
		payload = self.email.get_payload(*args, **kwargs)
		if isinstance(payload, list):
			return MultipartPayload(payload, self)
		else:
			return payload
	
	@property
	def parts(self):
		"It's mainly for for-loop iteration."
		if self.email.is_multipart():
			return MultipartPayload(self.email._payload, self)
		else:
			return ()
	
	def set_payload(self, *args, **kwargs):
		self.size_approx = None
		return self.email.set_payload(*args, **kwargs)
	
	def append_encoded_payload(self, encpayload):
		if self.is_multipart():
			raise PayloadTypeError('This is a MIME multipart message')
		self.size_approx = None
		self.email._payload += encpayload
	
	def is_multipart(self):
		return self.email.is_multipart()
	
	def get_charset(self):
		return self.email.get_charset()
	
	def set_charset(self, *args, **kwargs):
		return self.email.set_charset(*args, **kwargs)
	
	def get_content_charset(self):
		return self.email.get_content_charset()
	
	@property
	def content_type(self):
		return ContentTypeString(self.email.get_content_type())
	
	def get_filename(self):
		return self.email.get_filename()
	
	def set_type(self, *args, **kwargs):
		return self.email.set_type(*args, **kwargs)
	
	@property
	def preamble(self):
		return self.email.preamble
	
	@preamble.setter
	def preamble(self, s):
		self.email.preamble = s
	
	@property
	def epilogue(self):
		return self.email.epilogue
	
	@epilogue.setter
	def epilogue(self, s):
		self.email.epilogue = s
	
	
	@property
	def size_approx(self):
		if self._size_approx is None:
			size_approx = 0
			if self.is_multipart():
				for part in self.parts:
					size_approx += part.size_approx
			else:
				size_approx = len(self.email._payload)
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
				return int(len(self.email._payload) * 0.75)
			else:
				return len(self.email.get_payload(decode=True))
	
	def attach(self, attachment):
		self.size_approx = None
		if not isinstance(attachment, self.__class__):
			attachment = self.__class__(attachment, self)
			# TODO: what if this attachment is attached to multiple envelopes at once
		self.email.attach(attachment)
	
	def prepend_part(self, part):
		self.size_approx = None
		if not isinstance(part, self.__class__):
			part = self.__class__(part, self)
		self.email._payload = [part] + self.email._payload


class MultipartPayload(list):
	"this class represents email payload and maintains the parent email object's registered size when changing payloads in place"
	
	def __init__(self, payload_obj, email_obj):
		super(self.__class__, self).__init__(payload_obj)
		self._payload_obj = payload_obj
		self._email_obj = email_obj
		# let type checking done by the called methods, not us
	
	def __setitem__(self, itemname, item):
		self._email_obj.size_approx = None
		return self._payload_obj.__setitem__(itemname, item)
	
	def __delitem__(self, itemname):
		self._email_obj.size_approx = None
		return self._payload_obj.__delitem__(itemname)
	
	def __getitem__(self, itemname):
		item = self._payload_obj.__getitem__(itemname)
		# if any MIME part happens not to be also a gemlv.email.Email object,
		# then wrap it around and replace. it may happen when loading the email
		# object by eg. email.message_from_file or email.message_from_string.
		if not isinstance(item, self._email_obj.__class__):
			item = self._email_obj.__class__(item)
			self._payload_obj.__setitem__(itemname, item)
		return item
	
	def __getslice__(self, *_p):
		raise NotImplementedError()
	
	def __delslice__(self, *_p):
		raise NotImplementedError()
	
	def __setslice__(self, *_p):
		raise NotImplementedError()
	
	def __iter__(self):
		return ItemIterator(self)
	
	def remove(self, item):
		self._email_obj.size_approx = None
		return self._payload_obj.remove(item)
	
	def pop(self, *p):
		self._email_obj.size_approx = None
		return self._payload_obj.pop(*p)
	
	def insert(self, index, item):
		self._email_obj.size_approx = None
		return self._payload_obj.insert(index, item)

