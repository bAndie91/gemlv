
install:
	cp -va usr/share/applications/gemlv.desktop /usr/share/applications/
	cp -va usr/share/applications/gemlv-compose.desktop /usr/share/applications/
	cp -va gemlv /usr/bin/
	ln -snvf gemlv /usr/bin/gemlv-compose
	ln -snvf gemlv /usr/bin/gemlv-mailto
	cp -va gemlv-report gemlv-report-spam gemlv-report-ham /usr/bin/
	[ -d /etc/gemlv ] || mkdir /etc/gemlv
	cp -va filters.conf /etc/gemlv/
	for f in usr/share/locale/*/LC_MESSAGES/gemlv.po; \
	do msgfmt -o /"$$(basename "$$f" .po)".mo "$$f"; \
	done

uninstall:
	rm -v /usr/share/applications/gemlv.desktop
	rm -v /usr/share/applications/gemlv-compose.desktop
	rm -v /usr/bin/gemlv
	rm -v /usr/bin/gemlv-compose /usr/bin/gemlv-mailto
	rm -v /usr/bin/gemlv-report /usr/bin/gemlv-report-spam /usr/bin/gemlv-report-ham
	rm -v /etc/gemlv/filters.conf
	rmdir -v /etc/gemlv || true
	rm -v /usr/share/locale/*/LC_MESSAGES/gemlv.mo
