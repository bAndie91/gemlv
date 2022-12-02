#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import gtk

class EventImage(gtk.EventBox):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.image = gtk.Image()
		self.image.set_alignment(0, 0)
		self.add(self.image)
	def clear(self):
		return self.image.clear()
	def set_from_pixbuf(self, *args):
		return self.image.set_from_pixbuf(*args)
	def set_from_file(self, *args):
		return self.image.set_from_file(*args)
	def set_from_file_at_size(self, path, w, h):
		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(path, w, h)
		self.image.set_from_pixbuf(pixbuf)
	def set_size_request(self, *args):
		return self.image.set_size_request(*args)
	@property
	def size(self):
		pb = self.image.get_pixbuf()
		return pb.get_width(), pb.get_height()
	@property
	def width(self):
		return self.size[0]
	@property
	def height(self):
		return self.size[1]
	@property
	def pixbuf(self):
		return self.image.get_pixbuf()
	@pixbuf.setter
	def pixbuf(self, pb):
		self.image.set_from_pixbuf(pb)
	def redraw(self):
		self.pixbuf = self.pixbuf
	def set_padding(self, x, y):
		self.image.set_padding(x, y)
