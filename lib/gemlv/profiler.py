#!/usr/bin/env python

import time
import traceback
import sys

class timed(object):
	def __init__(self, threshold_sec, comment=''):
		self.comment = comment
		self.threshold_sec = threshold_sec
	def __call__(self, user_func):
		timer = self
		def timed_wrap(*p, **kw):
			t0 = time.time()
			r = user_func(*p, **kw)
			t1 = time.time()
			delta = t1-t0
			sys.stderr.write("** %s %.2f %s\n" % (user_func.__name__, delta, timer.comment))
			if timer.threshold_sec is not None and delta > timer.threshold_sec:
				sys.stderr.write("** function call was too slow, see traceback:\n")
				traceback.print_stack()
			return r
		
		return timed_wrap
