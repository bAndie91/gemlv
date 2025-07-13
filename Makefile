
LIB_PREFIX = /usr/lib/python2.7

.PHONY: default
default:
	@echo "maybe interested in: install, install-libs, locales"
	@false

.PHONY: install
install: install-libs install-locales install-desktop-files
	cp -v --no-preserve=ownership gemlv /usr/bin/
	ln -snvf gemlv /usr/bin/gemlv-compose
	ln -snvf gemlv /usr/bin/gemlv-mailto
	cp -v --no-preserve=ownership emlv-report /usr/bin/
	cp -v --no-preserve=ownership gemlv-report /usr/bin/
	cp -v --no-preserve=ownership gemlv-report-spam /usr/bin/
	cp -v --no-preserve=ownership gemlv-report-ham /usr/bin/
	mkdir -p /usr/libexec/gemlv
	cp -v --no-preserve=ownership scan-participants /usr/libexec/gemlv/
	mkdir -p /usr/libexec/gemlv/mailto-progs
	cp -v --no-preserve=ownership mailto-progs/kmail /usr/libexec/gemlv/mailto-progs/
	
	mkdir -p /etc/gemlv
	cp -v --no-preserve=ownership filters.ini /etc/gemlv/
	
	cp -v --no-preserve=ownership emlv /usr/bin/
	
	mkdir -p /usr/share/doc/gemlv
	cp -v --no-preserve=ownership LICENSE /usr/share/doc/gemlv/
	cp -v --no-preserve=ownership README.md /usr/share/doc/gemlv/
	
	git describe --tags > /usr/share/doc/gemlv/VERSION
	git show -s --format=%H > /usr/share/doc/gemlv/COMMIT


DESKTOP_FILES = \
  usr/share/applications/gemlv.desktop \
  usr/share/applications/gemlv-compose.desktop \
  usr/share/xfce4/helpers/gemlv.desktop \
  usr/share/menu/gemlv
DESKTOP_FILE_TARGETS = $(addprefix /,$(DESKTOP_FILES))

.PHONY: install-desktop-files
install-desktop-files: $(DESKTOP_FILE_TARGETS)
	update-desktop-database
	update-menus
$(DESKTOP_FILE_TARGETS): /%: %
	cp -v --no-preserve=ownership $< $@


LIB_FILES = $(shell find lib/gemlv/ -name '*.py' -printf '%P ')
LIB_TARGETS = $(addprefix $(LIB_PREFIX)/gemlv/,$(LIB_FILES))

.PHONY: install-libs
install-libs: $(LIB_TARGETS)
$(LIB_TARGETS): | $(LIB_PREFIX)/gemlv
$(LIB_PREFIX)/gemlv:
	mkdir -p $@
$(LIB_TARGETS): $(LIB_PREFIX)/gemlv/%: lib/gemlv/%
	rsync -Pviltx --mkpath $< $@


I18N_FILES = $(patsubst %.po,%.mo,$(wildcard usr/share/locale/*/LC_MESSAGES/gemlv.po))

.PHONY: locales
locales: $(I18N_FILES)
$(I18N_FILES): %.mo: %.po
	msgfmt -o $@ $<

I18N_TARGETS = $(addprefix /,$(I18N_FILES))

.PHONY: install-locales
install-locales: $(I18N_TARGETS)
$(I18N_TARGETS): /%: %
	cp -v --no-preserve=ownership $< $@


.PHONY: uninstall
uninstall:
	[ ! -e /usr/share/applications/gemlv.desktop ] || rm -v /usr/share/applications/gemlv.desktop
	[ ! -e /usr/share/applications/gemlv-compose.desktop ] || rm -v /usr/share/applications/gemlv-compose.desktop
	[ ! -e /usr/share/xfce4/helpers/gemlv.desktop ] || rm -v /usr/share/xfce4/helpers/gemlv.desktop
	[ ! -e /usr/share/menu/gemlv ] || rm -v /usr/share/menu/gemlv
	
	[ ! -e /usr/bin/gemlv ] || rm -v /usr/bin/gemlv
	[ ! -e /usr/bin/gemlv-compose ] || rm -v /usr/bin/gemlv-compose
	[ ! -e /usr/bin/gemlv-mailto ] || rm -v /usr/bin/gemlv-mailto
	[ ! -e /usr/bin/emlv-report ] || rm -v /usr/bin/emlv-report
	[ ! -e /usr/bin/gemlv-report ] || rm -v /usr/bin/gemlv-report
	[ ! -e /usr/bin/gemlv-report-spam ] || rm -v /usr/bin/gemlv-report-spam
	[ ! -e /usr/bin/gemlv-report-ham ] || rm -v /usr/bin/gemlv-report-ham
	[ ! -e /usr/libexec/gemlv/scan-participants ] || rm -v /usr/libexec/gemlv/scan-participants
	[ ! -e /usr/libexec/gemlv/mailto-progs/kmail ] || rm -v /usr/libexec/gemlv/mailto-progs/kmail
	rmdir -v /usr/libexec/gemlv/mailto-progs || true
	rmdir -v /usr/libexec/gemlv || true
	rm -v -r $(LIB_PREFIX)/gemlv/
	
	[ ! -e /etc/gemlv/filters.ini ] || rm -v /etc/gemlv/filters.ini
	[ ! -e /etc/gemlv ] || rmdir -v /etc/gemlv
	
	[ ! -e /usr/bin/emlv ] || rm -v /usr/bin/emlv
	
	[ ! -e /usr/share/doc/gemlv/LICENSE ] || rm -v /usr/share/doc/gemlv/LICENSE
	[ ! -e /usr/share/doc/gemlv/VERSION ] || rm -v /usr/share/doc/gemlv/VERSION
	[ ! -e /usr/share/doc/gemlv/COMMIT ]  || rm -v /usr/share/doc/gemlv/COMMIT
	[ ! -e /usr/share/doc/gemlv/ ] || rmdir -v /usr/share/doc/gemlv/
	
	rm -v /usr/share/locale/*/LC_MESSAGES/gemlv.mo


.PHONY: install-for-user
install-for-user:
	cp usr/share/applications/gemlv.desktop ~/.local/share/applications/
	cp usr/share/applications/gemlv-compose.desktop ~/.local/share/applications/
	update-desktop-database ~/.local/share/applications/
	mkdir -p ~/.config/gemlv/
	cp filters.ini ~/.config/gemlv/


.PHONY: uninstall-for-user
uninstall-for-user:
	[ ! -e ~/.local/share/applications/gemlv-compose.desktop ] || rm ~/.local/share/applications/gemlv-compose.desktop
	[ ! -e ~/.local/share/applications/gemlv.desktop ] || rm ~/.local/share/applications/gemlv.desktop
	update-desktop-database ~/.local/share/applications/
	[ ! -e ~/.config/gemlv/filters.ini ] || rm ~/.config/gemlv/filters.ini


.PHONY: install-deps
install-deps:
	apt install razor pyzor bogofilter
