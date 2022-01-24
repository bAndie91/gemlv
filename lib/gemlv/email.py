#!/usr/bin/env python2

import email

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

class Email(object):
	def __init__(self, email_obj):
		self.email = email_obj
	
	def __getitem__(self, item):
		return self.email.__getitem__(item)
	
	def __setitem__(self, item, x):
		return self.email.__setitem__(item, x)
	
	def __delitem__(self, item):
		return self.email.__delitem__(item)
	
	def get_all(self, *args, **kwargs):
		return self.email.get_all(*args, **kwargs)
	
	@property
	def _headers(self):
		return self.email._headers
	

	@timed
	def as_string(self):
		return self.email.as_string()
	
	@property
	def _payload(self):
		return self.email._payload
	
	def get_payload(self, *args, **kwargs):
		return self.email.get_payload(*args, **kwargs)
	
	
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
	
	def attach(self, *args, **kwargs):
		return self.email.attach(*args, **kwargs)

	def add_header(self, *args, **kwargs):
		return self.email.add_header(*args, **kwargs)

