#!/usr/bin/env python

def list2text(l):
	return ''.join(map(lambda x: x+'\n', l))

def human_size(x, suffix='B', decimals=1):
	prefixa = ['', 'K', 'M', 'G']
	for prefixum in prefixa:
		if abs(x) < 1024.0 or prefixum == prefixa[-1]:
			return '%.*f %s%s' % (decimals, x, prefixum, suffix)
		x /= 1024.0
