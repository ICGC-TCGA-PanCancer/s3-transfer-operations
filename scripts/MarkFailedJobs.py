#!/usr/bin/env python3

import argparse, os, re, subprocess, sys
import psycopg2

aparser = argparse.ArgumentParser(
    description='Determine the reason that a job has failed, and then move ' \
                'it to failed-jobs (or some other queue).')
aparser.add_argument('-s', '--search', dest='search', metavar='search_term',
    type=str, default='',
    help='a string to match in the failed job\'s stdout log.')
aparser.add_argument('-r', '--reason', dest='reason', metavar='failure_reason',
    type=str, default='unspecified',
    help='the failure reason corresponding to the search parameter.')
aparser.add_argument('-d', '--dest', dest='dest_queue', metavar='dest_queue',
    default='failed-jobs', type=str,
    help='the destination queue to move the JSON file to.')
aparser.add_argument('-f', '--force', dest='force', action='store_true',
    help='do not prompt for verification.')
aparser.add_argument('-os', '--oscript', dest='script', action='store_true',
    help='output the git commands as a script.')
args = aparser.parse_args()

# Configuration
S3TJ_ROOT_DIR = '/home/ubuntu/gitroot/s3-transfer-operations/'
S3TJ_SYS_DIR = 's3-transfer-jobs/'
DB_HOSTNAME = 'localhost'
DB_USERNAME = 'queue_user'
DB_PASSWORD = 'queue'
DB_NAME='queue_status'

# Return a Failure Reason (Commit Message)
def getFailureReason(ini, stdout, stderr):
    if (args.search != '') and (args.search in stdout):
        return 'unspecified' if (args.reason == 'unknown') else args.reason
    # EBI Repos Failure (2015-09-01)
    matchObj = re.search(r'"gnosServers"\s*:\s*"([\w\.\-\\/:]*)"', ini)
    if matchObj is not None:
        orig_match = 'gtrepo-ebi.annailabs.com' in matchObj.group(1)
    if orig_match: #and stdout_match
        return 'EBI Repos Failure'
    # BSC Repos Failure (2015-09-08)
    matchObj = re.search(r'"gnosServers"\s*:\s*"([\w\.\-\\/:]*)"', ini)
    if matchObj is not None:
        orig_match = 'gtrepo-bsc.annailabs.com' in matchObj.group(1)
    if orig_match: #and stdout_match
        return 'BSC Repos Failure'
    # OSDC Repos Failure (2015-09-08)
    matchObj = re.search(r'"gnosServers"\s*:\s*"([\w\.\-\\/:]*)"', ini)
    if matchObj is not None:
        orig_match = 'gtrepo-osdc-icgc.annailabs.com' in matchObj.group(1)
    if orig_match: #and stdout_match
        return 'OSDC Repos Failure'
    # Cannot Determine Cause
    return 'unknown'

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

# Establish Launcher DB Connection
try:
    conn = psycopg2.connect(
        'host=\'{}\' dbname=\'{}\' user=\'{}\' password=\'{}\''
            .format(DB_HOSTNAME, DB_NAME, DB_USERNAME, DB_PASSWORD))
except:
    sys.exit('[Fatal Error] Unable to connect to the launcher database.')

curs = conn.cursor()

# Retrieve a List of Failed Jobs
try:
    curs.execute('SELECT j.job_id, j.status, j.job_hash, j.ini, j.stdout, ' \
        'j.stderr, p.provision_id, p.provision_uuid, p.ip_address ' \
        'FROM job j, provision p ' \
        'WHERE j.job_uuid = p.job_uuid ' \
        'AND j.status IN (\'LOST\', \'FAILED\')')
    failed_jobs = curs.fetchall()
except Exception as e:
    sys.exit('[Fatal Error] {}.'.format(str(e)))

failure_count = 0

# Attempt to Find Files in Git Tracking Repos
git_instrs = []
git_instrs.append(['git', 'checkout', 'master'])
git_instrs.append(['git', 'reset', '--hard', 'origin/master'])
git_instrs.append(['git', 'pull'])
json_filenames = []
for job in failed_jobs:
    matchObj = re.search(r'"JSONfileName"\s*:\s*"([\w\.\-]*)"', job[3])
    json_filename = matchObj.group(1)

    # Remove if Duplicate of Previous Failure
    if json_filename in json_filenames: continue
    json_filenames.append(json_filename)

    # Remove if Re-run of Job Active
    try:
        curs.execute('SELECT COUNT(ini) FROM job ' \
            'WHERE ini LIKE \'%{}%\'' \
            'AND status NOT IN (\'LOST\', \'FAILED\')'.format(json_filename))
        active_count = curs.fetchone()[0]
    except Exception as e:
        sys.exit('[Fatal Error] {}.'.format(str(e)))
    if active_count > 0: continue

    # Search for File in Subqueues
    for root, subdirs, files in os.walk(S3TJ_ROOT_DIR + S3TJ_SYS_DIR):
        if ((json_filename in files) and
                not(root.endswith('backlog-jobs') or
                    root.endswith('queued-jobs') or
                    root.endswith('failed-jobs') or
                    root.endswith('completed-jobs'))):
            matchObj = re.search(r'^.*/(.*)$', root)
            job_stage = matchObj.group(1)
            fail_reason = getFailureReason(job[3], job[4], job[5])
            dest_queue = args.dest_queue
            if ((args.search == '') or
                    ((args.search != '') and (fail_reason == args.reason))):
                if not(args.script):
                    print('[Job ID: {}]'.format(str(job[0])))
                    print('-> IP Address: {} (possibly inactive)'
                            .format(job[8]))
                    print('-> Found corresponding JSON file in an ' \
                            'inconsistent stage ({}).'.format(job_stage))
                    if not(args.force):
                        fail_reason_in = input('-> Failure Reason ({}): '
                                        .format(fail_reason))
                        if fail_reason_in != '':
                            fail_reason = fail_reason_in
                        dest_queue_in = input('-> Destination Queue ({}): '
                                        .format(dest_queue))
                        if dest_queue_in != '':
                            dest_queue = dest_queue_in
                    else:
                        print('-> Failure Reason: {}'.format(fail_reason))
                        print('-> Destination Queue: {}'.format(dest_queue))

                src_path = './' + os.path.join(root[len(S3TJ_ROOT_DIR):],
                                        json_filename)
                dest_path = './' + S3TJ_SYS_DIR + args.dest_queue + '/'
                commit_msg = '[Failed] {} ({}): {}'.format(job_stage,
                                                        fail_reason,
                                                        json_filename)
                git_instrs.append(['git', 'mv', src_path, dest_path])
                git_instrs.append(['git', 'commit', '-m', commit_msg])
                failure_count += 1
            break
git_instrs.append(['git', 'push'])
if not(args.script): print('Total Failed Jobs: {}'.format(failure_count))

# Close DB Connection
curs.close()
conn.close()

# Print or Execute Git Instructions
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
    if len(git_instrs) > 4:
        print('Execution is disabled in the code. Run with \'-os\' flag to ' \
                'output script to console.')
        # try:
        #     print('Executing Git instructions... ', end='')
        #     subprocess.check_call(instr, stdout=open(os.devnull, 'w'),
        #                             stderr=open(os.devnull, 'w'))
        #     print('Done.')
        # except CalledProcessError:
        #     sys.exit('[Fatal Error] Git returned a non-zero status code.')
    else:
        print('No failed jobs found in active queues, nothing to do.')
