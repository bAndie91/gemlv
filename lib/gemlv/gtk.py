#!/usr/bin/env python2

import gtk
import glib

class Window(gtk.Window):
	def set_icon_name(self, name):
		self.set_icon(gtk.icon_theme_get_default().load_icon(name, gtk.ICON_SIZE_SMALL_TOOLBAR, 0))

class ScrolledLabelView(gtk.ScrolledWindow):
	def __init__(self, text=None):
		super(self.__class__, self).__init__()
		self.label = gtk.Label()
		self.label.set_alignment(0, 0)
		self.label.set_selectable(True)
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.add_with_viewport(self.label)
		if text is not None:
			self.set_text(text)
	def set_text(self, text):
		self.label.set_markup('<tt>' + glib.markup_escape_text(text) + '</tt>')

class LabelsToolItem(gtk.ToolItem):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.box = gtk.HBox()
		self.add(self.box)
	def set_labels(self, labels):
		for label in self.box.get_children():
			label.destroy()
		first = True
		for piece in labels:
			if not first:
				self.box.pack_start(gtk.SeparatorToolItem(), True, False)
			label = gtk.Label()
			if type(piece) == str:
				label.set_text(piece)
			elif type(piece) == dict:
				if piece.has_key('markup'):
					label.set_markup(piece['markup'])
				elif piece.has_key('text'):
					label.set_markup(piece['text'])
			self.box.pack_start(label, True, False)
			first = False
		self.box.show_all()

class StockToggleToolButton(gtk.ToggleToolButton):
	def __init__(self, stock=None):
		super(self.__class__, self).__init__(stock)
		if stock not in gtk.stock_list_ids():
			self.set_icon_name(stock)

class StockMenuItem(gtk.ImageMenuItem):
	def __init__(self, stock_id=None, icon_name=None, accel_group=None, label=None):
		super(self.__class__, self).__init__(stock_id=stock_id, accel_group=accel_group)
		if label is not None:
			self.set_label(label)
		if icon_name is not None:
			i = gtk.Image()
			i.set_from_icon_name(icon_name, gtk.ICON_SIZE_MENU)
			self.set_image(i)

class StockToolButton(gtk.ToolButton):
	def __init__(self, label=None, stock=None, tooltip=None):
		super(self.__class__, self).__init__()
		if stock is not None:
			if stock in gtk.stock_list_ids():
				if stock is not None: self.set_stock_id(stock)
			else:
				self.set_icon_name(stock)
		if label is not None:
			self.set_label(label)
		if tooltip is not None:
			self.set_tooltip_text(tooltip)
	def set_pixbuf(self, pxb):
		btn = self.get_children()[0]
		x = btn.get_children()[0]
		img, x = x.get_children()
		img.set_from_pixbuf(pxb)
		img.props.visible = True
	def __get_children(self):
		align = self.get_children()[0]
		hbox = align.get_children()[0]
		return hbox.get_children()
	def set_markup(self, markup):
		lbl = self.__get_children()[1]
		lbl.set_markup(markup)

class StockButton(gtk.Button):
	def __init__(self, label=None, stock=None, use_underline=True, icon_size=None):
		if stock is not None and stock in gtk.stock_list_ids():
			stock_tmp = stock
		else:
			stock_tmp = gtk.STOCK_ABOUT
		super(self.__class__, self).__init__(stock=stock_tmp, use_underline=use_underline)
		if label is not None:
			self.set_markup(label)
		if stock is None:
			self.set_icon('')
		elif stock not in gtk.stock_list_ids():
			self.set_icon(stock)
		if icon_size is not None:
			self.set_icon(stock, icon_size)
	def __get_children(self):
		align = self.get_children()[0]
		hbox = align.get_children()[0]
		return hbox.get_children()
	def set_label(self, label):
		x, lbl = self.__get_children()
		lbl.set_label(label)
	def set_markup(self, label):
		x, lbl = self.__get_children()
		lbl.set_markup(label)
	def set_icon(self, icon, size=gtk.ICON_SIZE_BUTTON):
		img, x = self.__get_children()
		if type(icon) == str:
			if icon == '':
				img.props.visible = False
			else:
				img.set_from_icon_name(icon, size)
				img.props.visible = True
		else:
			img.set_from_pixbuf(icon)
			img.props.visible = True
