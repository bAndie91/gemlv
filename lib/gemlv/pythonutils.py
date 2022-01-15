#!/usr/bin/env python2

class BasicReuseable():
	def __init__(self, value):
		self.value = value
	def __enter__(self):
		return self.value
	def __exit__(self, exc_type, exc_value, exc_traceback):
		pass

class Cyclelist(list):
	def __init__(self, lst, **kvargs):
		if type(lst) != type([]):
			raise TypeError('need list, %s found' % (str(type(lst))))
		if len(lst) < 1:
			raise ValueError('need non-empty list')
		super(self.__class__, self).__init__(lst)
		self.idx = 0
		if kvargs.has_key('at'):
			self.whirl(kvargs['at'])
	
	def whirl(self, val):
		for i in range(0, len(self)):
			if self[i] == val:
				self.idx = i
				return val
		return None
	
	def turn(self, n=1):
		self.idx = (self.idx + n) % len(self)
		return self[self.idx]
	
	def __getitem__(self, i):
		return super(self.__class__, self).__getitem__(i % len(self))

	def __setitem__(self, i, v):
		return super(self.__class__, self).__setitem__(i % len(self), v)
	
	def __str__(self):
		return str(self[self.idx])
