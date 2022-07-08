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

class ItemIterator(object):
	def __init__(self, obj):
		self.obj = obj
		self.index = -1
	
	def next(self):
		self.index += 1
		if self.index >= len(self.obj):
			raise StopIteration
		return self.obj.__getitem__(self.index)
	
	def __del__(self):
		pass

class SubstractableList(list):
	def __sub__(self, reductor):
		return SubstractableList([item for item in self if item not in reductor])
	
	def __rsub__(self, reductand):
		return SubstractableList([item for item in reductand if item not in self])

class DefaultingDict(dict):
	def set_default_value(self, v):
		self._default_value = v
	
	def __getitem__(self, key):
		return super(DefaultingDict, self).get(key, self._default_value)

class CaseInsensitiveDict(dict):
	def _to_canonical_key(self, userkey):
		if hasattr(userkey, 'lower'):
			key_lc = userkey.lower()
			for ckey in self.keys():
				if ckey.lower() == key_lc:
					return ckey
		return userkey
	
	def __getitem__(self, key):
		return super(CaseInsensitiveDict, self).__getitem__(self._to_canonical_key(key))
	
	def get(self, key, *fallback):
		return super(CaseInsensitiveDict, self).get(self._to_canonical_key(key), *fallback)
	
	def __delitem__(self, key):
		return super(CaseInsensitiveDict, self).__delitem__(self._to_canonical_key(key))
	
	def has_key(self, key):
		return super(CaseInsensitiveDict, self).has_key(self._to_canonical_key(key))
	
	def __contains__(self, key):
		return super(CaseInsensitiveDict, self).__contains__(self._to_canonical_key(key))
	
	def __setitem__(self, key, value):
		return super(CaseInsensitiveDict, self).__setitem__(self._to_canonical_key(key), value)
	
	def setdefault(self, *p, **kw):
		raise NotImplementedError
	
	def update(self, *p, **kw):
		raise NotImplementedError

class MultikeyUnionlistDict(dict):
	"""
	Example:
	
		d = MultikeyUnionlistDict(a=[1,2], b=[3,4], c=[5,6])
		d[('a','c')] --> [1,2,5,6]
	"""
	def __getitem__(self, key):
		if isinstance(key, (list, tuple)):
			keys = key
			assert all([ hasattr(self[key], '__iter__') for key in keys ])
			result = []
			return reduce(lambda result, key: (result.extend(self[key]), result)[1], keys, result)
		else:
			return super(MultikeyUnionlistDict, self).__getitem__(key)

def strip_list(alist):
	return [x.strip() for x in alist]

def compact(alist):
	return filter(None, alist)

class CaseInsensitiveString(str):
	def __repr__(self):
		return '%s(%s)' % (self.__class__.__name__, str.__repr__(self))
	def __eq__(self, p):
		try: p = p.lower()
		except: return NotImplemented
		return self.lower().__eq__(p)
	def __ne__(self, p):
		try: p = p.lower()
		except: return NotImplemented
		return not self.__eq__(p)
	def __lt__(self, p):
		try: p = p.lower()
		except: return NotImplemented
		return self.lower().__lt__(p)
	def __le__(self, p):
		try: p = p.lower()
		except: return NotImplemented
		return self.lower().__le__(p)
	def __gt__(self, p):
		try: p = p.lower()
		except: return NotImplemented
		return self.lower().__gt__(p)
	def __ge__(self, p):
		try: p = p.lower()
		except: return NotImplemented
		return self.lower().__ge__(p)
	def __contains__(self, p):
		try: p = p.lower()
		except: return NotImplemented
		return self.lower().__contains__(p)
	def endswith(self, *p):
		try: p0 = p[0].lower()
		except (IndexError, AttributeError): pass
		return self.lower().endswith(p0, *p[1:])
	def find(self, *p):
		try: p0 = p[0].lower()
		except (IndexError, AttributeError): pass
		return self.lower().find(p0, *p[1:])
	def index(self, *p):
		try: p0 = p[0].lower()
		except (IndexError, AttributeError): pass
		return self.lower().index(p0, *p[1:])
	def lstrip(self, *p, **kw):
		raise NotImplementedError
	def replace(self, *p, **kw):
		raise NotImplementedError
	def rfind(self, *p):
		try: p0 = p[0].lower()
		except (IndexError, AttributeError): pass
		return self.lower().rfind(p0, *p[1:])
	def rindex(self, *p):
		try: p0 = p[0].lower()
		except (IndexError, AttributeError): pass
		return self.lower().rindex(p0, *p[1:])
	def rsplit(self, *p, **kw):
		raise NotImplementedError
	def rstrip(self, *p, **kw):
		raise NotImplementedError
	def split(self, *p, **kw):
		raise NotImplementedError
	def startswith(self, *p):
		try: p0 = p[0].lower()
		except (IndexError, AttributeError): pass
		return self.lower().startswith(p, *p[1:])
	def strip(self, *p, **kw):
		raise NotImplementedError
	def translate(self, *p, **kw):
		raise NotImplementedError
