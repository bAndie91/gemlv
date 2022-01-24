#!/usr/bin/env python2

import email

class Email(object):
	def __init__(self, email_obj):
		self.email = email_obj
	
	def __getitem__(self, item):
		return self.email.__getitem__(item)
	
	def get_all(self, *args, **kwargs):
		return self.email.get_all(*args, **kwargs)

	@property
	def _headers(self):
		return self.email._headers
	
	
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
