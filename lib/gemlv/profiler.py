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
