__author__ = 'nbyrne'

import codecs
import json
import pystache
import os
import sys


# USAGE: json2ini.py [input json file] [output folder]
# Creates an ini file in the designated output folder

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

    # Fix thhe gnos server output to be compatible with ini file format
    handlebars['gnosserver'] = str(','.join(json_data[u'gnos_repo']))

    # Make the final hash substitution
    for files in json_data[u'files']:
        if str(files[u'file_name']) == (handlebars['analysisid'] + ".xml"):
            handlebars['xmlhash'] = str(files[u'file_md5sum'])
    with codecs.open(template, 'r', 'utf-8') as f:
        template_data = f.read()
    # Final INI File
    final_data = pystache.render(template_data, handlebars)
    #print final_data # For debugging
    with codecs.open(os.path.join(output_folder, os.path.basename(json_input)) + ".ini", "w", 'utf-8') as f:
        f.write(final_data)

    sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "USAGE: json2ini.py [input json file] [template file] [output folder]"
        print ""
        sys.exit(1)
    main()
