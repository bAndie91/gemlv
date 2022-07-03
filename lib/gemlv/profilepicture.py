#!/usr/bin/env python2

import hashlib
import urllib2
import glib
import gtk.gdk

def load_gravatar(email_address, gtk_container, gemlv_props):
	url_templ = gemlv_props['avatar/url_template'] or 'https://www.gravatar.com/avatar/{email_lc_md5}?default=404&size=64&rating=G'
	tmpl_vars = {
		'email': email_address,
		'email_lc': email_address.lower(),
		'email_md5': hashlib.md5(email_address).hexdigest(),
		'email_lc_md5': hashlib.md5(email_address.lower()).hexdigest(),
	}
	url = url_templ.format(**tmpl_vars)
	# TODO: retry with (1) lowercase domain and (2) lowercase localpart (eventhough email address localpart is case sensitive)
	try:
		web = urllib2.urlopen(url)
	except urllib2.HTTPError:
		pass
	else:
		loader = gtk.gdk.PixbufLoader()
		try:
			loader.write(web.read())
			loader.close()
		except glib.GError as e:
			if e.code != 3:   # 'Unrecognized image file format'
				raise
		else:
			pxb = loader.get_pixbuf()
			img = gtk_container.children()[0]
			img.set_from_pixbuf(pxb)
			img.set_data('source', email_address)
			gtk_container.show_all()
