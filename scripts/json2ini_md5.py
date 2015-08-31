__author__ = 'nbyrne'

import codecs
import hashlib
import json
import pystache
import os
import sys
import urllib2

# USAGE: json2ini.py [input json file] [output folder]
# Creates an ini file in the designated output folder

# Constants
REPO_WHITELIST="/home/ubuntu/s3-transfer-operations/repo-whitelist.txt"

def md5_valid(url, md5):

    # Fetch Metadata
    try:
        response = urllib2.urlopen(url)
        data = response.read()
        response.close()
    except:
        print >> sys.stderr, "GNOS Not responding to metadata query"
        return False

    # Verify the md5sum of the file, same format as download_check.py
    datasplit = data.split('\n')
    datasplit[1] = "<ResultSet>"
    data = "\n".join(datasplit).rstrip()
    hasher = hashlib.md5()
    hasher.update(data)
    myhash=hasher.hexdigest()

    if md5 != myhash:
        print "ERROR: The xml data downloaded from %s does not match the pregenerated data!" % sys.argv[1]
        print "ERRPR: Expected %s, calculated %s" % (md5, myhash)
        print >> sys.stderr, "ERROR: The xml data downloaded from %s does not match the pregenerated data!" % sys.argv[1]
        return False

    return True

def main():
    json_input = sys.argv[1]
    template = sys.argv[2]
    output_folder = sys.argv[3]

    with open(json_input) as f:
        json_data = f.read()

    json_data = json.loads(json_data)

    # Create relationships between a mustache dictionary and our json data
    handlebars = {}
    mapping_dictionary = {
        'donorid': u'submitter_donor_id',
        'projectcode': u'project_code',
        'analysisid': u'gnos_id'
    }

    # Substitute the data
    for item, value in mapping_dictionary.iteritems():
        handlebars[item] = str(json_data[value])

    # Store the json filename in the mustache object
    handlebars['filename'] = os.path.basename(sys.argv[1])
    
    # Create the QUEUE System Hash Value from Junjun's SOP
    handlebars['hash'] = '.'.join(handlebars['filename'].split('.')[1:])

    # Fix the gnos server output to be compatible with ini file format
    handlebars['gnosserver'] = str(','.join(json_data[u'gnos_repo']))

    # Fail to generate ini if the gnos-server is not in the whitelist:
    with open(REPO_WHITELIST) as f:
	whitelist = f.read().split('\n')
    whitelisted = False
    for repo in whitelist:
	print repo
	if repo[0] == "#":
		continue
	else:
		if repo.strip() in handlebars['gnosserver']:
			whitelisted = True
			break

    if not whitelisted:
	print "Not producing an INI file for this JSON as the repo is not whitelisted."
	sys.exit(1)

    # Make the final hash substitution
    for files in json_data[u'files']:
        if str(files[u'file_name']) == (handlebars['analysisid'] + ".xml"):
            handlebars['xmlhash'] = str(files[u'file_md5sum'])

	# Before going any further, do an md5 check on the real data
    url = handlebars['gnosserver'].split(',')[0] + "cghub/metadata/analysisFull/" + handlebars['analysisid']
    md5 = handlebars['xmlhash']
    if not md5_valid(url, md5):
        # Error handler for bad JSON file
        print ">>> Bad md5 XML sum in this file!"
	sys.exit(9)

    with codecs.open(template, 'r', 'utf-8') as f:
        template_data = f.read()
    # Final INI File
    final_data = pystache.render(template_data, handlebars)
    #print final_data # For debugging
    with codecs.open(os.path.join(output_folder, os.path.basename(json_input)) + ".ini", "w", 'utf-8') as f:
        f.write(final_data)
    print ">>> File written!"
    sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "USAGE: json2ini.py [input json file] [template file] [output folder]"
        print ""
        sys.exit(1)
    main()
