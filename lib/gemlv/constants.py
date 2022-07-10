#!/usr/bin/env python
# -*- coding: utf-8 -*-

from contenttypestring import ContentTypeString

COMMON_MULTIPART_PREAMBLE = "This is a multi-part message in MIME format."  # @notranslate

RE_DOMAIN = r'(?:(?!-)[a-z\d-]+(?<!-)\.?)+'
RE_IPADDR = r'[0-9a-f\.:]+'
RE_DOMAINPART = r'(?P<DP>' + RE_DOMAIN + '|\[' + RE_IPADDR + '\])'
RE_EMAIL_PERMISSIVE = r'.@' + RE_DOMAINPART
RE_EMAIL = r'(?P<LP>\w[\w\.+-]*(?<![\.-]))@' + RE_DOMAINPART
RE_ADDRESS = r'\s*(?:(?P<DQ>\x22|)(?P<N>(?<=\x22)(?:[^\x22\n\\]|\\[\x22\\])*|[^\x22\x27<\n\\]+)(?P=DQ))?\s*(?(N)<|(?:(?P<LT><)|))' + RE_EMAIL + '(?(N)>|(?(LT)>))\s*(?:,\s*|$)'

PMU_MIME = '<i><span color=\'gray30\'>'
PMU_MIME_CLOSE = '</span></i>'
PMU_NAME = '<b>'
PMU_NAME_CLOSE = '</b>'
PMU_HEAD = '<b>'
PMU_HEAD_CLOSE = '</b>'
PMU_WARN = '<span foreground=\'darkred\' weight=\'bold\'>'
PMU_WARN_CLOSE = '</span>'
PMU_SUBJ = '<big>'
PMU_SUBJ_CLOSE = '</big>'
PMU_AUTOCOMPLETION_MATCH_CHAR = '<b><u>%s</u></b>'
PMU_ADDRESSBOOK_ADDED_ADDRESS = '<i><span color=\'gray30\'>%s</span></i>'
PMU_ADDRESSBOOK_NOT_ADDED_ADDRESS = '%s'

HDR_CT = 'Content-Type'
HDR_CD = 'Content-Disposition'
HDR_CTE = 'Content-Transfer-Encoding'
HDR_DNT = 'Disposition-Notification-To'
HDR_GDR = 'Generate-Delivery-Report'
HDR_PNDR = 'Prevent-NonDelivery-Report'
HDR_OR = 'Original-Recipient'
HDR_MID = 'Message-ID'
HDR_REF = 'References'
HDR_XSD = 'X-Sent-Date'
HDR_XQID = 'X-Queue-ID'
HDR_SUBJ = 'Subject'


MIMETYPE_OCTETSTREAM = ContentTypeString('application/octet-stream')
MIMETYPE_EMAIL = ContentTypeString('message/rfc822')
MIMETYPE_URILIST = ContentTypeString('text/uri-list')
MIMETYPE_TEXT = ContentTypeString('text/plain')
MIMETYPE_HTML = ContentTypeString('text/html')
MIMETYPE_SYMLINK = ContentTypeString('inode/symlink')
MIMETYPE_HEADERS = ContentTypeString('text/rfc822-headers')
MIMETYPE_DN = ContentTypeString('message/disposition-notification')

XATTR_CHARSET = 'user.mime_encoding'
XATTR_TYPE = 'user.mime_type'
XATTR_ORIGIN = 'user.xdg.origin.email.message-id'
XATTR_SUBJECT = 'user.xdg.origin.email.subject'
XATTR_FROM = 'user.xdg.origin.email.from'
XATTR_MDNSENT = 'user.gemlv.mdn-sent-in'
XATTR_REPLIED = 'user.gemlv.replied-in'
XATTR_FORWARDED = 'user.gemlv.forwarded-in'
XATTR_QUEUEID = 'user.gemlv.sent.queue-id'

ENCNAMES_UUE = ('x-uuencode', 'uuencode', 'uue', 'x-uue')

SUBJECT_PREFIX_FWD, SUBJECT_PREFIX_RE = range(2)

MULTIPART_INDEX_PGP_ENCRYPTED_V1 = 1  # see RFC 3156

SYMBOL_BULLET = '•'
SYMBOL_EMAIL = '✉'
SYMBOL_WEB = '☛'

default_avatar_url_templates = [
	'https://{avatars_sec_host}/avatar/{email:md5}',
	'https://{avatars_sec_host}/avatar/{email:lower:md5}',
	'http://{avatars_host}/avatar/{email:md5}',
	'http://{avatars_host}/avatar/{email:lower:md5}',
	'https://www.gravatar.com/avatar/{email:md5}?default=404&size=64&rating=G',
	'https://www.gravatar.com/avatar/{email:lower:md5}?default=404&size=64&rating=G',
]
