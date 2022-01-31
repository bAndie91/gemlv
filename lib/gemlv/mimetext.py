#!/usr/bin/env python

class MimeCoded(unicode):
	def __init__(self, x):
		# None becomes '' here
		if x is None: x = ''
		super(unicode, self).__init__(x)

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
