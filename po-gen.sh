#!/bin/bash

export TEXTDOMAINDIR=usr/share/locale/
file=gemlv

for langdir in "$TEXTDOMAINDIR"/*
do
	lang=`basename "$langdir"`
	grep -Pon '".+?(?<!\\)"' "$file" |\
	{
	declare -A new
	while IFS=: read -r lno text
	do
		if sed -ne ${lno}p "$file" | grep -q @notranslate
		then
			continue
		fi
		
		text=`echo -n "$text" | sed -e 's/^"//; s/"$//;'`
		if [ -z "${new[$text]}" ]
		then
			msgid=${text//\\n/$'\n'}
			if [ "$(LANGUAGE=$lang gettext gemlv "$msgid")" = "$msgid" ]
			then
				new[$text]=1
				echo "# file: $file, line: $lno"
				echo "msgid \"$text\""
				echo "msgstr \"\""
				echo
			fi
		fi
	done
	}
done
