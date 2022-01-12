
import sys

def warnx(string):
	sys.stderr.write(string + ('' if string[-1] == '\n' else '\n'))

