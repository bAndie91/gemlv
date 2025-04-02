#!/usr/bin/env python2

import gtk
import glib
from gemlv.constants import *
import gobject
import re
from pythonutils import coalesce

MOUSE_BUTTON_LEFT = 1
MOUSE_BUTTON_MIDDLE = 2
MOUSE_BUTTON_RIGHT = 3

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
	__gsignals__ = {
		'labels-updated': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, ()),
	}
	def __init__(self, labels=[]):
		super(self.__class__, self).__init__()
		self.box = gtk.HBox()
		self.labels = []
		self.set_labels(labels)
	def set_labels(self, labels):
		"""
		sets multiple labels separated by a separator widget.
		parameter: labels
		  list of labels, each label is either a string, or a dict.
		  if string, then set it literally (no pango markup);
		  if dict, 2 keys considered:
		    key 'markup': set it as pango markup text,
		    key 'text': set it as literal text.
		"""
		for label in self.box.get_children():
			label.destroy()
		if len(labels) == 1:
			lbl = self.make_label(labels[0])
			self.replace_child(lbl)
			self.labels = [lbl]
		else:
			self.replace_child(self.box)
			first = True
			for piece in labels:
				label = self.make_label(piece)
				if not first:
					self.box.pack_start(gtk.SeparatorToolItem(), True, False)
				self.box.pack_start(label, True, False)
				first = False
			self.labels = self.box.get_children()
		self.show_all()
		self.emit('labels-updated')
	def make_label(self, labeldef):
		label = gtk.Label()
		if isinstance(labeldef, basestring):
			label.set_text(labeldef)
		elif isinstance(labeldef, dict):
			if labeldef.has_key('markup'):
				label.set_markup(labeldef['markup'])
			elif labeldef.has_key('text'):
				label.set_text(labeldef['text'])
		else:
			label.set_text(repr(labeldef))
		label.set_alignment(0, 0.5)
		return label
	def replace_child(self, child):
		children = self.get_children()
		if len(children) > 0:
			if children[0] != child:
				self.remove(children[0])
			else:
				return
		self.add(child)

class StockToggleToolButton(gtk.ToggleToolButton):
	def __init__(self, stock=None):
		super(self.__class__, self).__init__(stock)
		if stock not in gtk.stock_list_ids():
			self.set_icon_name(stock)

class Toolbar(gtk.Toolbar):
	def append_items(self, items):
		for it in items:
			self.insert(it, -1)

class StockToolIcon(gtk.ToolItem):
	def __init__(self, iconname, tooltiptext=None, toolbar=None):
		super(self.__class__, self).__init__()
		self.set_border_width(3)
		self.add(gtk.image_new_from_icon_name(iconname, toolbar.get_icon_size() if toolbar is not None else gtk.ICON_SIZE_SMALL_TOOLBAR))
		self.set_tooltip_text(tooltiptext)

class SeparatorToolItem(gtk.SeparatorToolItem):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.set_draw(True)
		self.set_expand(False)

class SpacerToolItem(gtk.SeparatorToolItem):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.set_draw(False)
		self.set_expand(True)

class StockToolButton(gtk.ToolButton):
	def __init__(self, label=None, stock=None, tooltip=None):
		super(gtk.ToolButton, self).__init__()
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

class BaseActionToolItem(object):
	@staticmethod
	def _preinit(label, iconname, tooltip):
		iconlabel = None
		stock = gtk.stock_lookup(iconname)
		if stock: iconlabel = re.sub('_', '', stock[1])  # remove shortcut key from button label
		label = coalesce(label, iconlabel, tooltip)
		tooltip = coalesce(tooltip, label, iconlabel)
		return (label, tooltip)
	
	def _config(self, actions, iconname, label):
		act_left_click, act_right_click = actions[:]
		if act_left_click is not None:
			connect_loopless_signal(self, 'clicked', *act_left_click)
		if act_right_click is not None:
			connect_loopless_signal(self.child, 'button-press-event', *act_right_click)
		self.set_data('stock', iconname)
		self.set_data('label', label)

class ActionStockToolButton(BaseActionToolItem, StockToolButton):
	def __init__(self, actions=(None, None), label=None, iconname=None, tooltip=None):
		(label, tooltip) = BaseActionToolItem._preinit(label, iconname, tooltip)
		super(self.__class__, self).__init__(label=label, stock=iconname, tooltip=tooltip)
		self._config(actions, iconname, label)

class ActionMenuToolButton(BaseActionToolItem, gtk.MenuToolButton):
	def __init__(self, actions=(None, None), label=None, iconname=None, tooltip=None):
		super(self.__class__, self).__init__(iconname)
		(label, tooltip) = BaseActionToolItem._preinit(label, iconname, tooltip)
		self.set_label(label)
		self.set_tooltip_text(tooltip)
		self._config(actions, iconname, label)

class Menu(gtk.Menu):
	def remove_all_menuitems(self):
		for mi in self.get_children():
			self.remove(mi)
	def append_menuitems(self, items):
		for mi in items:
			self.append(mi)

class StockMenuItem(gtk.ImageMenuItem):
	def __init__(self, stock_id=None, icon_name=None, accel_group=None, label=None, config=[]):
		super(self.__class__, self).__init__(stock_id=stock_id, accel_group=accel_group)
		if label is not None:
			self.set_label(label)
		if icon_name is not None:
			i = gtk.Image()
			i.set_from_icon_name(icon_name, gtk.ICON_SIZE_MENU)
			self.set_image(i)
		for step in config:
			method = getattr(self, step[0])
			method(*step[1])

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

class Scrollable(gtk.ScrolledWindow):
	def __init__(self, child):
		assert isinstance(child, gtk.Widget)
		super(self.__class__, self).__init__()
		self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
		self.add_with_viewport(child)
		self.set_shadow_type(gtk.SHADOW_NONE)
		viewport = self.get_child()
		viewport.connect('scroll-event', self.scroll_viewport)
	
	def set_shadow_type(self, shadow_type):
		viewport = self.get_child()
		viewport.set_shadow_type(shadow_type)
	
	def scroll_viewport(self, viewport, event):
		hadj = self.get_hadjustment()
		delta = +10 if event.direction in [gtk.gdk.SCROLL_DOWN, gtk.gdk.SCROLL_LEFT] else -10
		newvalue = hadj.value + delta
		width = self.get_allocation().width
		if newvalue + width > hadj.upper:
			newvalue = hadj.upper - width
		hadj.set_value(newvalue)
	
	def scroll_to_focused_widget(self):
		adjust = self.get_vadjustment()
		focused = self.get_toplevel().get_focus()
		
		if focused is not None:
			foc_left, foc_top = focused.translate_coordinates(self.child, 0, 0)
			foc_bottom = foc_top + focused.get_allocation().height
			top = adjust.value
			bottom = top + adjust.page_size
			if foc_top < top:
				adjust.value = foc_top
			elif foc_bottom > bottom:
				adjust.value = foc_bottom - adjust.page_size

class ComboBoxEntry(gtk.ComboBoxEntry):
	def get_value(self):
		"return the selected entry if any, otherwise the typed text"
		it = self.get_active_iter()
		if it is not None:
			return self.get_model().get_value(it, self.get_text_column())
		else:
			return self.child.get_text()
	def set_text(self, newtext):
		"set the user-input text (regardless of that equivalent text is in the drop-down list or not)"
		self.child.set_text(newtext)

class Clock(gtk.HBox):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.spin_hour = gtk.SpinButton()
		self.spin_minute = gtk.SpinButton()
		self.spin_second = gtk.SpinButton()
		self.spin_hour.set_range(0, 23)
		self.spin_minute.set_range(0, 59)
		self.spin_second.set_range(0, 59)
		self.spin_hour.set_increments(1, 6)
		self.spin_minute.set_increments(1, 15)
		self.spin_second.set_increments(1, 15)
		self.spin_hour.set_wrap(True)
		self.spin_minute.set_wrap(True)
		self.spin_second.set_wrap(True)
		self.spin_hour.set_numeric(True)
		self.spin_minute.set_numeric(True)
		self.spin_second.set_numeric(True)
		self.select_time()
		self.pack_start(self.spin_hour, False, False)
		self.pack_start(gtk.Label(':'), False, False)
		self.pack_start(self.spin_minute, False, False)
		self.pack_start(gtk.Label(':'), False, False)
		self.pack_start(self.spin_second, False, False)
		self.show_all()
	
	def select_time(self, ts=None):
		import time
		t = time.localtime(ts)
		self.spin_hour.set_value(t.tm_hour)
		self.spin_minute.set_value(t.tm_min)
		self.spin_second.set_value(t.tm_sec)
	
	def get_time(self):
		return (self.spin_hour.get_value_as_int(), self.spin_minute.get_value_as_int(), self.spin_second.get_value_as_int())


def add_key_binding(widget, keyname, callback):
	accelgroup = gtk.AccelGroup()
	key, modifier = gtk.accelerator_parse(keyname)
	accelgroup.connect_group(key, modifier, gtk.ACCEL_VISIBLE, callback)
	widget.add_accel_group(accelgroup)

def get_current_window():
	for w in gtk.window_list_toplevels():
		if w.is_active():
			while True:
				par = w.get_transient_for()
				if par is None:
					return w
				else:
					w = par
	return None

def add_gtk_icon_to_stock(icon_name, label_str_localized):
	gtk.stock_add([(icon_name, label_str_localized, 0, 0, None)])
	iconsource = gtk.IconSource()
	iconsource.set_icon_name(icon_name)
	iconset = gtk.IconSet()
	iconset.add_source(iconsource)
	icon_factory = gtk.IconFactory()
	icon_factory.add(icon_name, iconset)
	icon_factory.add_default()

def get_stock_icon_by_mime(main, sub):
	assoc_main = {
		'multipart': gtk.STOCK_DIRECTORY,
		'message': 'emblem-mail',
	}
	assoc_full = {
		'application/pgp-signature': 'mail-signed',
		'application/ics': 'x-office-calendar',
		'text/calendar': 'x-office-calendar',
		'inode/directory': gtk.STOCK_DIRECTORY,
		'inode/x-empty': 'document-new',
		'multipart/digest': 'emblem-mail',
	}
	full = main + '/' + sub
	
	if assoc_full.has_key(full):
		return assoc_full[full]
	elif assoc_main.has_key(main):
		return assoc_main[main]
	
	if full in [MIMETYPE_HTML]:
		return main + '-' + sub
	elif main in ['audio', 'image', 'font', 'package', 'text', 'video']:
		return main + '-x-generic'
	
	return gtk.STOCK_FILE

def coordinates(widget, corner):
	assert isinstance(corner, gtk.CornerType)
	X, Y = widget.window.get_origin()
	x, y, w, h = widget.get_allocation()
	if corner == gtk.CORNER_TOP_LEFT:
		return (X + x, Y + y, True)
	elif corner == gtk.CORNER_TOP_RIGHT:
		return (X + x + w, Y + y, True)
	elif corner == gtk.CORNER_BOTTOM_LEFT:
		return (X + x, Y + y + h, True)
	elif corner == gtk.CORNER_BOTTOM_RIGHT:
		return (X + x + w, Y + y + h, True)

class TreeStore(gtk.TreeStore):
	@property
	def iter_recursive(self):
		return TreeStoreIterator(self)

class TreeStoreIterator(object):
	def __init__(self, treestore):
		self.treestore = treestore
		self.path = (0,)
	
	def __iter__(self):
		return self
	
	def next(self):
		try:
			row = self.treestore[self.path]
		except IndexError:
			if len(self.path) > 1:
				self.path = self.path[:-2] + (self.path[-2] + 1,)
				return next(self)
			else:
				raise StopIteration
		else:
			self.path = self.path + (0,)
			return row.iter
	
	def __del__(self):
		pass

def _call_loopless_handler(*args):
	args = list(args)
	data = args.pop()
	func = args.pop()
	target_widget = args[0]
	user_data = data['user_data']
	args.extend(user_data)
	handler = data['handler-id']
	target_widget.handler_block(handler)
	result = func(*args)
	target_widget.handler_unblock(handler)
	return result

def connect_loopless_signal(gobject, signal_name, func, *user_data):
	"""
	This function together with call_loopless_handler() manages to call
	a signal handler function without recursion into itself.
	"""
	data = {'user_data': user_data}
	handler = gobject.connect(signal_name, _call_loopless_handler, func, data)
	data['handler-id'] = handler
