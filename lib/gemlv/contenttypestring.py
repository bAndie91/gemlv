#!/usr/bin/env python

class ContentTypeString(str):
	def __init__(self, v):
		v = v.lower()
		super(self.__class__, self).__init__(v)
		self.main, self.sub = v.split('/')
