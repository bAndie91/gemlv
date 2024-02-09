
LIB_PREFIX = /usr/lib/python2.7

default:
	@echo "maybe interested in: install, install-libs, locales"
	@false

install: install-libs locales
	cp -v --no-preserve=ownership usr/share/applications/gemlv.desktop /usr/share/applications/
	cp -v --no-preserve=ownership usr/share/applications/gemlv-compose.desktop /usr/share/applications/
	cp -v --no-preserve=ownership usr/share/xfce4/helpers/gemlv.desktop /usr/share/xfce4/helpers/
	cp -v --no-preserve=ownership usr/share/menu/gemlv /usr/share/menu/
	
	update-desktop-database
	update-menus
	
	cp -v --no-preserve=ownership gemlv /usr/bin/
	ln -snvf gemlv /usr/bin/gemlv-compose
	ln -snvf gemlv /usr/bin/gemlv-mailto
	cp -v --no-preserve=ownership gemlv-report /usr/bin/
	cp -v --no-preserve=ownership gemlv-report-spam /usr/bin/
	cp -v --no-preserve=ownership gemlv-report-ham /usr/bin/
	mkdir -p /usr/libexec/gemlv
	cp -v --no-preserve=ownership scan-participants /usr/libexec/gemlv/
	mkdir -p /usr/libexec/gemlv/mailto-progs
	cp -v --no-preserve=ownership mailto-progs/kmail /usr/libexec/gemlv/mailto-progs/
	
	mkdir -p /etc/gemlv
	cp -v --no-preserve=ownership filters.conf /etc/gemlv/
	
	cp -v --no-preserve=ownership emlv /usr/bin/
	
	mkdir -p /usr/share/doc/gemlv
	cp -v --no-preserve=ownership LICENSE /usr/share/doc/gemlv/
	
	git describe --tags > /usr/share/doc/gemlv/VERSION
	git show -s --format=%H > /usr/share/doc/gemlv/COMMIT

install-libs:
	mkdir -p $(LIB_PREFIX)/gemlv
	cp -v --no-preserve=ownership -r lib/gemlv/*.py $(LIB_PREFIX)/gemlv/

locales:
	for f in usr/share/locale/*/LC_MESSAGES/gemlv.po; \
	do \
	  msgfmt -o "$${f%.*}".mo "$$f"; \
	done

uninstall:
	[ ! -e /usr/share/applications/gemlv.desktop ] || rm -v /usr/share/applications/gemlv.desktop
	[ ! -e /usr/share/applications/gemlv-compose.desktop ] || rm -v /usr/share/applications/gemlv-compose.desktop
	[ ! -e /usr/share/xfce4/helpers/gemlv.desktop ] || rm -v /usr/share/xfce4/helpers/gemlv.desktop
	[ ! -e /usr/share/menu/gemlv ] || rm -v /usr/share/menu/gemlv
	
	[ ! -e /usr/bin/gemlv ] || rm -v /usr/bin/gemlv
	[ ! -e /usr/bin/gemlv-compose ] || rm -v /usr/bin/gemlv-compose
	[ ! -e /usr/bin/gemlv-mailto ] || rm -v /usr/bin/gemlv-mailto
	[ ! -e /usr/bin/gemlv-report ] || rm -v /usr/bin/gemlv-report
	[ ! -e /usr/bin/gemlv-report-spam ] || rm -v /usr/bin/gemlv-report-spam
	[ ! -e /usr/bin/gemlv-report-ham ] || rm -v /usr/bin/gemlv-report-ham
	[ ! -e /usr/libexec/gemlv/scan-participants ] || rm -v /usr/libexec/gemlv/scan-participants
	[ ! -e /usr/libexec/gemlv/mailto-progs/kmail ] || rm -v /usr/libexec/gemlv/mailto-progs/kmail
	rmdir -v /usr/libexec/gemlv/mailto-progs || true
	rmdir -v /usr/libexec/gemlv || true
	rm -v -r $(LIB_PREFIX)/gemlv/
	
	[ ! -e /etc/gemlv/filters.conf ] || rm -v /etc/gemlv/filters.conf
	[ ! -e /etc/gemlv ] || rmdir -v /etc/gemlv
	
	[ ! -e /usr/bin/emlv ] || rm -v /usr/bin/emlv
	
	[ ! -e /usr/share/doc/gemlv/LICENSE ] || rm -v /usr/share/doc/gemlv/LICENSE
	[ ! -e /usr/share/doc/gemlv/VERSION ] || rm -v /usr/share/doc/gemlv/VERSION
	[ ! -e /usr/share/doc/gemlv/COMMIT ]  || rm -v /usr/share/doc/gemlv/COMMIT
	[ ! -e /usr/share/doc/gemlv/ ] || rmdir -v /usr/share/doc/gemlv/
	
	rm -v /usr/share/locale/*/LC_MESSAGES/gemlv.mo

install-for-user:
	cp usr/share/applications/gemlv.desktop ~/.local/share/applications/
	cp usr/share/applications/gemlv-compose.desktop ~/.local/share/applications/
	update-desktop-database ~/.local/share/applications/
	mkdir -p ~/.config/gemlv/
	cp filters.conf ~/.config/gemlv/

uninstall-for-user:
	[ ! -e ~/.local/share/applications/gemlv-compose.desktop ] || rm ~/.local/share/applications/gemlv-compose.desktop
	[ ! -e ~/.local/share/applications/gemlv.desktop ] || rm ~/.local/share/applications/gemlv.desktop
	update-desktop-database ~/.local/share/applications/
	[ ! -e ~/.config/gemlv/filters.conf ] || rm ~/.config/gemlv/filters.conf
