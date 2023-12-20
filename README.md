# gemlv
Email viewer and composer for email files, in GTK

- [Screenshots](#screenshots)
- [Features](#features)
- [Autocrypt implementation status](#autocrypt-implementation-status)
- [CLI options](#cli-options)
- [Compatibility](#compatibility)
- [FAQ](#faq)
- [Inspiration](#inspiration)

## Screenshots

![email viewer](img/gemlv-read-email.jpg)
![view html email](img/gemlv-read-html.jpg)
![simple addressbook](img/gemlv-compose-simple-addressbook.jpg)
![composer context menu](img/gemlv-compose-menu-and-attachments.jpg)
![address auto completion](img/gemlv-address-auto-completion.jpg)

## Features

- display headers
	- only which are significant for end-users
	- toggle "show all headers"
	- highlight email addresses
	- convert Date to local timezone
	- Reply-By and Expires headers, show warning if time is over
- view plain text message, or a filtered attachment
	- configure multiple filters for non-text attachments
	- change font or turn monospace on/off, font zoom, preserve selected font
	- wrap lines, wrap letters, no wrap
	- show link for Content-Location if applicable
- display attachments and other MIME parts in tree view
	- select first text/plain or text/html part at beginning
	- show attached filenames, and their mime type
	- Drag-and-Drop from attachment panel
- email parts (attachments) can be opened with external program ([mimeopen-gui](https://github.com/bAndie91/mimeopen-gui))
- save attachments (MIME parts)
	- save as:
		- single files
		- more files at once in a folder
		- preserving multipart structure (ie. save in directory tree)
	- preverse modification time, permissions if specified in attachment (Content-Disposition header `modification_date` and `posix_mode` parameters respectively)
	- preserve symlinks
	- save Message-ID, Content-Type in Extended Attributes
- Encryption
	- decrypt encrypted Email when open (MIME/PGP format is supported)
	- verify GPG signatures, warn if mismatch
		- both attached signature and signature which is embedded in the pgp message
	- encrypt message and attachments before send (MIME/PGP format)
		- hide Bcc recipients in the encrypted message
		- obfuscate RFC822 headers and put their cleartext content in an inline `text/rfc822-headers` part (as per IETF draft-autocrypt-lamps-protected-headers-02)
	- sign email message and attachments (MIME/PGP)
	- set [Autocrypt](https://autocrypt.org) header
		- remove UIDs from the gpg public key which are not disclosed in the current email, so protecting these email addresses from leakage
	- sign and encrypt headers too (headers repeated both in the encapsulated email and in a `text/rfc822-headers` MIME part)
- [Libravatar](https://www.libravatar.org/) and [Gravatar](http://www.gravatar.com/) support
	- you can configure the URLs to fetch the avatar picture of the email sender:
		- files in precedence: `~/.config/gemlv/prop/avatar/url_templates.json`, `/etc/gemlv/prop/avatar/url_templates.json`
		- mini template-language to access email address, libravatar hostnames, lower-case, upper-case, hash, ...
	- save avatar picture with the source URL in xattributes
- remember UI elements size and position
- button to unsubscribe from newsletters, mailing lists
- report as spam/ham
	- supported spam-db networks and filters:
		- razor
		- pyzor
		- bogofilter
	- move Email file into / out from ```Spam``` folder
	- override spam-report command on user/system level (`~/.local/share/gemlv/report-spam`, `/etc/gemlv/report-spam`)
- writing Email
	- send by standard ```sendmail -ti``` command
		- can interrupt sending process
		- pass SENDMAIL_FROM and SENDMAIL_RCPT environment variables to help `sendmail` decide where to route (if your `sendmail` needs this)
	- you can add usual headers (From, Reply-To, To, Cc, Bcc) and arbitrary ones as well
		- email address syntax is validated
		- pick date and time from calendar when adding date-time headers
	- can edit message by external program ([mimeopen-gui](https://github.com/bAndie91/mimeopen-gui))
	- options
		- set Importance and Priority by a toolbar toggle
		- ask Disposition Notification by a toolbar toggle
	- addressbook
		- read plain email addresses from files line by line (`~/Mail/.addressbook` and `~/Mail/.addressbook.d/*`)
		- automatically save addresses to which you send emails (`~/Mail/.addressbook.d/gemlv.auto`)
		- auto completion on address fields
		- suggest "From" addresses based on past correspondences with the given recipients (need to run `scan-participants` regurarly to populate database)
	- auto save drafts to `~/.cache/gemlv/drafts/`
		- you can find and open draft emails there in case of something crashed
	- support `~/.signature` and multiple user signature files in `~/Mail/.signatures/*`
- reply options
	- consider Reply-To field
	- set References, In-Reply-To headers
	- quote plain text message in the new email
	- Reply To All: reply to sender, to all recipients, to the mailing list, except ourself
	- Reply To List
	- Forward: attach original email, not quote
	- send Disposition Notification voluntarily
		- even for messages have not explicitely requested it
		- it generates the response message conforming to the Accept-Language header (if gemlv translation is available)
	- store replied/forwarded/MDN-sent states in file Extended Attribute
- attachments in compose mode
	- attach files, symlinks and even whole directories recursively
		- by browsing them
		- by drag-and-drop
	- attach data blobs by drag-and-drop
	- rename attachments in place
	- remove, reorder attachments
	- use that Transport Encoding (quoted-printable, base64) which provides smaller encoded data for a given clear data
	- store file's modification time, POSIX permission bits in Content-Disposition header
- CLI options
	- viewer mode (```gemlv raw_email.eml```)
	- compose mode (```gemlv --compose```)
	- addresses (repeat for more recipients)
		- ```--from 'Anna Lastname <anna@example.net>'```
		- ```--to bud@example.net --to Carl\ \<carl@example.net\> --to '"Lastname, David" <dave@example.net>'```
		- ```--cc ...```
		- ```--bcc ...```
	- subject (```--subject "..."```)
	- message body (```--message "..."```)
	- attachments (```--attach file1 --attachment file2 --attach dir1/```)
	- full ```mailto``` link (```--mailto "mailto:%22Buddy%22%20%3Cbud@example.net%3E?subject=awesome%20email%20client"```), RFC2368, RFC6068
- hotkeys
	- ```Ctrl-Q``` Quit
	- ```Ctrl-W``` Close compose window
	- ```Ctrl-S``` Save attachment(s) in viewer mode; save draft in composer mode
	- ```Ctrl-Shift-S``` Save draft as...
	- ```Ctrl-O``` Open attachment with external program
	- ```Ctrl-N``` Compose new Email
	- ```Ctrl-Shift-R``` Reply
	- ```Ctrl-R``` Reply to All
	- ```Ctrl-F``` Forward message with envelope (headers and attachments)
	- ```Ctrl-Shift-F``` Forward message (body only)
	- ```Ctrl-U``` Filter/Unfilter rich text (non-plain text, eg: html, pdf, ...)
	- ```Ctrl-H``` Show/Hide uncommon headers
	- ```F4``` Edit draft message with external program
	- ```Alt-A``` Open built-in addressbook browser
	- ```Shift-Down``` Pop up auto completion (on header input boxes in composer mode)


## Autocrypt implementation status

- [ ] header parsing: compliant parsing of the Autocrypt header
- [ ] keygen: secret key generation follows Autocrypt UI guidance
	- call sensible GPG UI program to generate key
- [ ] peerstate: state is kept according to spec
- [X] header inject
	- gemlv sends Autocrypt header when crypto-sign is turned on
- [ ] recommend: implements Autocrypt recommendation
- [ ] encrypt: encrypts outgoing messages properly
	- [X] body
	- [X] headers
	- [X] attachments
- [ ] setup message: proper generation and processing of Autocrypt Setup Message
- [ ] setup process: follows guidance with respect to Autocrypt account setup
- [ ] gossip
	- [ ] send Autocrypt-Gossip headers
	- [ ] process incoming Autocrypt and Autocrypt-Gossip headers
- [ ] uid decorative: UID in key data is only used for decorative purposes, and in particular not for looking up keys for an e-mail address.


## CLI options

```
usage: gemlv [-h] [--compose] [--from ADDRESS] [--to ADDRESS] [--cc ADDRESS]
             [--bcc ADDRESS] [--subject STRING] [--message STRING]
             [--mailto URL] [--attach FILE] [--localedir DIR]
             [--opener COMMAND] [--header STRING]
             [FILE]

positional arguments:
  FILE                  Raw Email file for read or continue editing (default:
                        None)

optional arguments:
  -h, --help            show this help message and exit
  --compose             Write a new Email (default: False)
  --from ADDRESS        New Email's writer's name and address (default: None)
  --to ADDRESS          New Email's Recipients, repeatable (default: None)
  --cc ADDRESS          Carbon Copy Recipients, repeatable (default: None)
  --bcc ADDRESS         Blind Carbon Copy Recipients, repeatable (default:
                        None)
  --subject STRING      Subject (default: None)
  --message STRING      Message body (default: None)
  --mailto URL          Full 'mailto:' link (default: None)
  --attach FILE, --attachment FILE
                        Attachment file's path, repeatable (default: None)
  --localedir DIR       L10n base directory (default: None)
  --opener COMMAND      File opener command (default: mimeopen-gui)
  --header STRING       Add custom header(s) to the new Email (default: None)
```

## Dependencies

not exhaustive list

- gnupg <https://github.com/isislovecruft/python-gnupg>
- pyxdg <https://www.freedesktop.org/wiki/Software/pyxdg/>

## Compatibility

### python gnupg module

[Gnupg](https://github.com/isislovecruft/python-gnupg) searches gpg-agent using `psutil`.
When procfs (`/proc`) is mounted with `hidepid` option, `psutil` throws AccessDenied,
which prevents `gnupg` to initialize.

Affected versions: `gnupg < 3.0.1`.
Recommended to install `gnupg >= 3.0.1`.

## FAQ

**Q.** Support feature-rich HTML-rendering?

**A.** No. HTML-rendering is a huge job on its own right; does not fit into one program - one job paradigm for me.
I built in filters for several media types (including html), you can define more filter for one mime type
as well. Though it's not capable of feature-rich rendering with images, css, interactive content, nor 
anything like that. There are embedable libs for this purpose out there, but I doubt any html renderer engine
can work on the long-term on one hand, and I don't belive any reasonable ground to send so full-featured html 
around in emails on the other hand (except as attachments which you can open externally or just save).

**Q.** Where can I configure incoming/outgoing email server address/hostname/portnumber/ssl/tls/starttls options?

**A.** Nowhere. It's just a viewer for raw email files (and composer). You may setup an other program to
acquire your emails and save them in a directory, or use some virtual filesystem (fuse) which represents your 
IMAP/POP3 mailbox as a conventional filesystem. I personally donwload my emails by `getmail4` preserving IMAP
folder structure.

**Q.** I get error when about to send email. Why?

**A.** Consult the docs of your `sendmail` installation. If you have not any, install a tool providing
`sendmail` command; there are more of them.

**Q.** Python 2 ?

**A.** Yes. It is not banned. Is it?

**Q.** How to edit the addressbook? The "Edit" button does not work…

**A.** The addressbook is just plain text files at `~/Mail/.addressbook`
and `~/Mail/.addressbook.d/*`, one address line (real name + email address) per line.
Edit it with any text editor. The "Edit" button runs the default file opener program to open
the addressbook file(s) for editing.

**Q.** When the composer window opens up the header field is frozen and I can not click on it.

**A.** It seems to be some sort of gtk bug. Just scroll over it and it thaws.

## Inspiration

Many UI parts are inspired by Sylpheed/Claws-mail.

