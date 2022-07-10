#!/usr/bin/env python2

import hashlib
import urllib2
import glib
import gtk.gdk
from gemlv.sysutils import warnx
import re
from gemlv.pythonutils import uniq

multi_url_host_delimiter = ' '

class RunAndCache(object):
	def __init__(self, func, *args, **kwargs):
		self.func = func
		self.args = args
		self.kwargs = kwargs
		self.result = None
	def __str__(self):
		if self.result is None:
			self.result = self.func(*self.args, **self.kwargs)
		return self.result

def libravatar_servers(srv_name):
	import dns.resolver
	import dns.exception
	dns.resolver.get_default_resolver()
	dns.resolver.default_resolver.port = 254
	try:
		answer = dns.resolver.query(srv_name, 'SRV')
	except dns.exception.DNSException:
		return ''
	else:
		return multi_url_host_delimiter.join(['%s:%d' % (item.target, item.port) for item in answer.rrset.items])

class UnknownTemplateVariable(Exception):
	pass

class UnknownTemplateFunction(Exception):
	pass

def template_replacer(expr, tmpl_vars):
	expr = expr.split(':')
	var = expr[0]
	filters = expr[1:]
	try:
		result = str(tmpl_vars[var])
	except KeyError:
		raise UnknownTemplateVariable(var)
	for fltr in filters:
		if fltr == 'lower':
			result = result.lower()
		elif fltr == 'upper':
			result = result.upper()
		elif fltr == 'md5':
			result = hashlib.md5(result).hexdigest()
		elif fltr == 'localpart':
			result = result.rsplit('@', 1)[0]
		elif fltr == 'domainpart':
			result = result.rsplit('@', 1)[1]
		else:
			raise UnknownTemplateFunction(fltr)
	return result

def load_avatar(email_address, gtk_container, url_templates):
	email_domain = email_address.rsplit('@', 1)[1]
	tmpl_vars = {
		'email': email_address,
		'avatars_host': RunAndCache(libravatar_servers, '_avatars._tcp.' + email_domain),
		'avatars_sec_host': RunAndCache(libravatar_servers, '_avatars-sec._tcp.' + email_domain),
	}
	avatar_ok = False
	urls_tried = []
	
	for url_template in url_templates:
		multi_url = re.sub(r'\{(.+?)\}', lambda match: template_replacer(match.group(1), tmpl_vars), url_template)
		multi_url_parts = urllib2.urlparse.urlparse(multi_url)
		hosts = multi_url_parts.netloc.split(multi_url_host_delimiter)
		for host in hosts:
			if host == '': continue
			url_parts = list(multi_url_parts)
			url_parts[1] = host
			url = urllib2.urlparse.urlunparse(url_parts)
			if url in urls_tried: continue
			urls_tried.append(url)
			
			try:
				web = urllib2.urlopen(url)
			except Exception as e:
				warnx(url + ': ' + str(e))
			else:
				loader = gtk.gdk.PixbufLoader()
				try:
					loader.write(web.read())
					loader.close()
				except Exception as e:
					warnx(url + ': ' + str(e))
				else:
					pxb = loader.get_pixbuf()
					img = gtk_container.children()[0]
					img.set_from_pixbuf(pxb)
					img.set_data('source', email_address)
					img.set_data('source-url', url)
					gtk_container.show_all()
					avatar_ok = True
			if avatar_ok:
				break
		if avatar_ok:
			break
