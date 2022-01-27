#!/usr/bin/env python2

import email
from gemlv.constants import *

# TODO: factor out this block
import time
import traceback
def timed(func):
	def timed_wrap(*p, **kw):
		t0 = time.time()
		r = func(*p, **kw)
		t1 = time.time()
		delta = t1-t0
		print "** %s %.2f" % (func.__name__, delta)
		if delta > 0.2:
			traceback.print_stack()
		return r
	return timed_wrap

class PayloadError(Exception):
	pass

class Email(object):
	def __init__(self, email_obj, parent_email_obj = None):
		self.email = email_obj
		self.parent = parent_email_obj
		self.origin_path = None
		self._size_approx = None
	
	def __getitem__(self, itemname):
		return self.email.__getitem__(itemname)
	
	def __setitem__(self, itemname, item):
		return self.email.__setitem__(itemname, item)
	
	def __delitem__(self, itemname):
		return self.email.__delitem__(itemname)
	
	def get_all(self, *args, **kwargs):
		return self.email.get_all(*args, **kwargs)
	
	@property
	def _headers(self):
		return self.email._headers
	
	def items(self):
		return self.email.items()
	
	@timed
	def as_string(self):
		return self.email.as_string()
	
	@property
	def _payload(self):
		if self.email.is_multipart():
			return MultipartPayload(self.email._payload, self.email)
		else:
			return self.email._payload
	
	def get_payload(self, *args, **kwargs):
		payload = self.email.get_payload(*args, **kwargs)
		if isinstance(payload, list):
			return MultipartPayload(payload, self.email)
		else:
			return payload
	
	def set_payload(self, *args, **kwargs):
		self.size_approx = None
		return self.email.set_payload(*args, **kwargs)
	
	def append_encoded_payload(self, encpayload):
		if self.is_multipart():
			raise PayloadError('This is a MIME multipart message')
		self.size_approx = None
		self.email._payload += encpayload
	
	def as_stream(self):
		from email.generator import Generator
		# TODO
	
	def is_multipart(self):
		return self.email.is_multipart()
	
	def get_content_type(self):
		return self.email.get_content_type()
	
	def get_content_maintype(self):
		return self.email.get_content_maintype()
	
	def get_content_subtype(self):
		return self.email.get_content_subtype()
	
	def get_content_charset(self):
		return self.email.get_content_charset()
	
	def get_filename(self):
		return self.email.get_filename()
	
	def set_type(self, *args, **kwargs):
		return self.email.set_type(*args, **kwargs)
	
	def set_param(self, *args, **kwargs):
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
	def parts(self):
		if self.email.is_multipart():
			return self.email._payload
		else:
			return []
	
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
	
	@timed
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
	
	def add_header(self, *args, **kwargs):
		return self.email.add_header(*args, **kwargs)
		
	def replace_header(self, *args, **kwargs):
		return self.email.replace_header(*args, **kwargs)


class MultipartPayload(list):
	"this class represents email payload and maintains the parent email object's registered size when changing payloads in place"
	
	def __init__(self, payload_obj, email_obj):
		# let type checking done by the called methods, not us
		self._payload_obj = payload_obj
		self._email_obj = email_obj
	
	def __setitem__(self, itemname, item):
		self._email_obj.size_approx = None
		return self._payload_obj.__setitem__(itemname, item)
	
	def __delitem__(self, itemname):
		self._email_obj.size_approx = None
		return self._payload_obj.__delitem__(itemname)
	
	def __getitem__(self, itemname):
		return self._payload_obj.__getitem__(itemname)
	
	def remove(self, item):
		self._email_obj.size_approx = None
		return self._payload_obj.remove(item)
	
	def insert(self, index, item):
		self._email_obj.size_approx = None
		return self._payload_obj.insert(index, item)
