#!/usr/bin/env python3

import argparse, hashlib, json, os, subprocess, sys, urllib
from os import listdir
from urllib import request

aparser = argparse.ArgumentParser(
    description='Compare the XML file MD5 hash asserted in the JSON file ' \
                'with the MD5 computed from downloading the XML file locally.')
aparser.add_argument('-d', '--dest', dest='dest_queue', metavar='dest_queue',
    default='failed-jobs', type=str,
    help='the destination queue to move the JSON file to.')
aparser.add_argument('-os', '--oscript', dest='script', action='store_true',
    help='output the git commands as a script.')
args = aparser.parse_args()

# Configuration
S3TJ_ROOT_DIR = '/home/ubuntu/gitroot/s3-transfer-operations/'
S3TJ_SYS_DIR = 's3-transfer-jobs/'

# GET Remote XML File and Calculate MD5 Hashsum
def get_GNOS_XML_MD5_hash(gnos_analysis_url):
    try:
        resp = urllib.request.urlopen(gnos_analysis_url)
        data = resp.read()
        resp.close()
    except:
        return ''
    data_split = data.decode('utf-8').split('\n')
    data_split[1] = '<ResultSet>'
    data = '\n'.join(data_split).rstrip().encode('utf-8')
    hasher = hashlib.md5()
    hasher.update(data)
    return hasher.hexdigest()

# Change Script Execution Context to Git Repository
os.chdir(S3TJ_ROOT_DIR)

# Pull s3-transfer-operations Git Repository
try:
    if not(args.script): print('Updating git repository... ', end='')
    subprocess.check_call(['git', 'pull'], stdout=open(os.devnull, 'w'),
                            stderr=open(os.devnull, 'w'))
    if not(args.script): print('Done.')
except CalledProcessError:
    sys.exit('[Fatal Error] Git returned a non-zero status code.')

# Iterate Through All JSON Files
base_dir = S3TJ_ROOT_DIR + S3TJ_SYS_DIR + 'queued-jobs/'
json_files = [rst for rst in listdir(base_dir)
                if (rst.endswith('.json') and os.path.isfile(base_dir + rst))]
git_instrs = []
git_instrs.append(['git', 'checkout', 'master'])
git_instrs.append(['git', 'reset', '--hard', 'origin/master'])
git_instrs.append(['git', 'pull'])
failure_count = 0
for filename in json_files:
    json_xml_md5 = ''
    gnos_analysis_url = ''
    gnos_xml_md5 = ''

    # Parse Each JSON File
    with open(base_dir + filename, 'r') as file:
        file_contents = file.read()
        json_contents = json.loads(file_contents)
        json_xml_md5 = ''
        for trans_fileObj in json_contents['files']:
            if trans_fileObj['file_name'].endswith('.xml'):
                json_xml_md5 = trans_fileObj['file_md5sum']
                break
        gnos_analysis_url = (json_contents['gnos_repo'][0] +
                        'cghub/metadata/analysisFull/' +
                        json_contents['gnos_id'])
    if not(json_xml_md5 and gnos_analysis_url):
            sys.exit('Fatal Error: Could not read XML MD5 hash and/or GNOS ' \
                        'Repos. URL from JSON file.')

    # GNOS XML MD5 Hashsum
    gnos_xml_md5 = get_GNOS_XML_MD5_hash(gnos_analysis_url)
    if not(gnos_xml_md5):
        print('Error: Could not reach GNOS server to retrieve XML analysis ' \
                'file, skipping MD5 comparison for: {}.'.format(filename))
        continue

    # Compare MD5 Hashsums
    if json_xml_md5 != gnos_xml_md5:
        failure_count += 1
        if not(args.script):
            print('JSON File: ' + filename)
            print('-> XML MD5 Hashsum Mismatch!')
            print('-> JSON XML MD5 (Local): {}'.format(json_xml_md5))
            print('-> GNOS XML MD5 (Remote): {}'.format(gnos_xml_md5))
        else:
            job_stage = 'queued-jobs'
            src_path = './' + S3TJ_SYS_DIR + 'queued-jobs/' + filename
            dest_path = './' + S3TJ_SYS_DIR + args.dest_queue + '/'
            fail_reason = 'XML MD5 Mismatch'
            commit_msg = '[Failed] {} ({}): {}'.format(job_stage,
                                                    fail_reason,
                                                    filename)
            git_instrs.append(['git', 'mv', src_path, dest_path])
            git_instrs.append(['git', 'commit', '-m', commit_msg])
git_instrs.append(['git', 'push'])

# Output Script or Summary
if args.script:
    if len(git_instrs) > 4:
        for instr in git_instrs:
            for arg in instr:
                if ' ' in arg:
                    print('\'{}\''.format(arg), end=' ')
                else:
                    print('{}'.format(arg), end=' ')
            print('')
else:
    print('Total Mismatches: {}'.format(failure_count))
    if failure_count == 0:
        print('No XML MD5 mismatches found, nothing to do.')
