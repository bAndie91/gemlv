#!/usr/bin/env python2

import hashlib
import urllib2
import glib
import gtk.gdk
from gemlv.sysutils import warnx
import re
from gemlv.pythonutils import uniq

multi_url_host_delimiter = ' '

default_avatar_url_templates = [
	'https://{avatars_sec_host}/avatar/{email:md5}',
	'https://{avatars_sec_host}/avatar/{localpart=email:localpart}{lowerdomain=email:domainpart:lower}{lowerdomain_email=localpart+"@"+lowerdomain}{lowerdomain_email:md5}',
	'https://{avatars_sec_host}/avatar/{email:lower:md5}',
	'http://{avatars_host}/avatar/{email:md5}',
	'http://{avatars_host}/avatar/{localpart=email:localpart}{lowerdomain=email:domainpart:lower}{lowerdomain_email=localpart+"@"+lowerdomain}{lowerdomain_email:md5}',
	'http://{avatars_host}/avatar/{email:lower:md5}',
	'https://www.gravatar.com/avatar/{email:md5}?default=404&size=64&rating=G',
	'https://www.gravatar.com/avatar/{localpart=email:localpart}{lowerdomain=email:domainpart:lower}{lowerdomain_email=localpart+"@"+lowerdomain}{lowerdomain_email:md5}?default=404&size=64&rating=G',
	'https://www.gravatar.com/avatar/{email:lower:md5}?default=404&size=64&rating=G',
]

class LazyLoad(object):
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

def tvar(name, tmpl_vars):
	if name.startswith('"') and name.endswith('"'):
		return name[1:-1]
	return str(tmpl_vars[name])

def template_replacer(expr, tmpl_vars):
	"""
	this is a half-baked template language.
	template expressions are enclosed in curly brackets.
	all template expression consists of:
	
	- optional variable assignment, which is a variable name followed by an equal sign
	  - if there is an assignment, the template expression evaluates to an empty string
	- actual variable name, of which value is substituted in
	  - if there is a double-quote-enclosed string instead of a variable name, then the string is returned verbatim
	  - variable names (or double-quoted literals) can be concatenated by plus sign, so then the concatenated values are taken
	- zero or more filter keywords, preceeded by a colon per each
	  - filters are applied to the resulting value in chain
	  - valid filter keywords: lower, upper, md5, localpart, domainpart
	
	syntax roughly:
	
	[ASSIGN_VAR "="] <VAR | "LITERAL"> [+ <VAR | "LITERAL"> [+ <VAR | "LITERAL"> ...]] [: FILTER [: FILTER ...]]
	"""
	
	expr = expr.split(':')
	var = expr[0]
	filters = expr[1:]
	if '=' in var:
		lvalue, var = var.split('=', 1)
	else:
		lvalue = None
	
	try:
		if '+' in var:
			result = ''.join([tvar(x, tmpl_vars) for x in var.split('+')])
		else:
			result = tvar(var, tmpl_vars)
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
	if lvalue is not None:
		tmpl_vars[lvalue] = result
		return ''
	else:
		return result

def load_avatar(email_address, gtk_container, url_templates=None):
	if url_templates is None:
		url_templates = default_avatar_url_templates
	email_domain = email_address.rsplit('@', 1)[1]
	tmpl_vars = {
		'email': email_address,
		'avatars_host': LazyLoad(libravatar_servers, '_avatars._tcp.' + email_domain),
		'avatars_sec_host': LazyLoad(libravatar_servers, '_avatars-sec._tcp.' + email_domain),
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
