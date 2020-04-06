
import sys
import os
import gnupg

gpg = gnupg.GPG()

message = open(sys.argv[0]).read()
signature = open(sys.argv[1]).read()

sgn_r, sgn_w = os.pipe()
sgn_fh = os.fdopen(sgn_w, 'w')
sgn_fh.write(signature)
sgn_fh.close()

v = gpg.verify_data('/dev/fd/%d'%sgn_r, message)
d = v.__dict__
del d['gpg']
import json
print json.dumps(d, indent=2)
