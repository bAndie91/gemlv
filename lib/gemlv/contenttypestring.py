#!/usr/bin/env python

class ContentTypeString(str):
	def __init__(self, v):
		super(self.__class__, self).__init__(v)
		self._value = v
		self.main, self.sub = v.split('/')
