Author | Date
--- | ---
bAndie91 | 2017-05-28T08:57:10Z

in email reader mode I Drag multiple rows from attachments, but just the first one get Dropped.
any chance to implement multi-DnD?

I intentionally don't say "multifile-DnD" because those attachments are not real files in filesystem, which I can point to by URIs. that's why I can not use text/uri-list for Drop Source target.
They get DnD'ed by mixed XDirectSave and application/octet-stream methods.
Remote application usually demands for XDirectSave and acquires the Dragged file's name. Then gemlv reports that she could not perform the file saving ordered by XDS protocol. In next step the remote app usually falls back to demands for application/octet-stream, but at this time he knows the filename of the data blob.

---

Author | Date
--- | ---
bAndie91 | 2017-05-28T08:57:10Z

implemented by creating (and later removing) temporary files.
