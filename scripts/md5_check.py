# Python download checker

import hashlib
import sys
import urllib2

def main(url, md5):

    # Fetch Metadata
    response = urllib2.urlopen(url)
    data = response.read()
    response.close()

    # Verify the md5sum of the file, same format as download_check.py
    datasplit = data.split('\n')
    datasplit[1] = "<ResultSet>"
    data = "\n".join(datasplit).rstrip()
    hasher = hashlib.md5()
    hasher.update(data)
    myhash=hasher.hexdigest()

    # Store the patched xml, for filing by the workflow
    with open("patched.xml","w") as f:
	f.write(data)

    if md5 != myhash:
	print "ERROR: The xml data downloaded from %s does not match the pregenerated data!" % sys.argv[1]
	print "ERRPR: Expected %s, calculated %s" % (md5, myhash)
	print >> sys.stderr, "ERROR: The xml data downloaded from %s does not match the pregenerated data!" % sys.argv[1]
	sys.exit(1)

    sys.exit(0)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

# USAGE: python md5_check.py [https://metadataURL] [md5sum of xml]
