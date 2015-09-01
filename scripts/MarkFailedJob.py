#!/usr/bin/python3

import argparse, os, re, subprocess, sys
import psycopg2

aparser = argparse.ArgumentParser(
    description='Determine the reason that a job has failed, and then move ' \
                'it to failed-jobs.')

aparser.add_argument('-f', '--force', dest='force', action='store_true',
    help='do not prompt for verification when a job\'s reason for failure is ' \
            '\'unknown\'.')
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
    # EBI Repos Failure (2015-09-01)
    matchObj = re.search(r'"gnosServers"\s*:\s*"([\w\.\-\\/:]*)"', ini)
    if matchObj is not None:
        orig_match = 'gtrepo-ebi.annailabs.com' in matchObj.group(1)
    if orig_match:
        return 'EBI Repos Failure'
    # Cannot Determine Cause
    return 'unknown'

# Change Script Execution Context to Git Repository
os.chdir(S3TJ_ROOT_DIR)

# Pull s3-transfer-operations Git Repository
try:
    print('Updating git repository... ', end='')
    subprocess.check_call(['git', 'pull'], stdout=open(os.devnull, 'w'),
                            stderr=open(os.devnull, 'w'))
    print('Done.')
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
        'WHERE j.job_uuid = p.job_uuid and j.status = \'FAILED\'')
    failed_jobs = curs.fetchall()
except Exception as e:
    sys.exit('[Fatal Error] {}.'.format(str(e)))
curs.close()
conn.close()

# Pull the local git repos
# ...

# Attempt to Find Files in Git Tracking Repos
git_instrs = []
git_instrs.append(['git', 'checkout', 'master'])
git_instrs.append(['git', 'reset', '--hard', 'origin/master'])
git_instrs.append(['git', 'pull'])
for job in failed_jobs:
    matchObj = re.search(r'"JSONfileName"\s*:\s*"(.*\.json)"', job[3])
    json_filename = matchObj.group(1)
    for root, subdirs, files in os.walk(S3TJ_ROOT_DIR + S3TJ_SYS_DIR):
        if ((json_filename in files) and
                not(root.endswith('queued-jobs') or
                    root.endswith('failed-jobs') or
                    root.endswith('completed-jobs'))):
            matchObj = re.search(r'^.*/(.*)$', root)
            job_stage = matchObj.group(1)
            print('[Job ID: {}]'.format(str(job[0])))
            print('IP Address: {} (possibly inactive)'.format(job[8]))
            print('Found corresponding JSON file in an inconsistent stage ({}).'
                .format(job_stage))
            fail_reason = getFailureReason(job[3], job[4], job[5])
            if not(args.force):
                fail_reason_in = input('Failure Reason ({}): '
                                .format(fail_reason))
                if fail_reason_in != '':
                    fail_reason = fail_reason_in
            else:
                print('Failure Reason: {}'.format(fail_reason))

            src_path = os.path.join(root, json_filename)
            dest_path = S3TJ_ROOT_DIR + S3TJ_SYS_DIR + 'failed-jobs/'
            commit_msg = '[Failed] {} ({}): {}'.format(job_stage,
                                                    fail_reason,
                                                    json_filename)
            git_instrs.append(['git', 'mv', src_path, dest_path])
            git_instrs.append(['git', 'commit', '-m', commit_msg])
            break
git_instrs.append(['git', 'push'])

# Execute Git Instructions
print('------------------------------------------------------------')
print('-- Simulated Instructions (nothing actually being run):   --')
print('-- Note: Spaces in arguments will be properly handled.    --')
print('------------------------------------------------------------')
for instr in git_instrs:
    print(' '.join(instr))
    # try:
    #     print('Executing Git instructions... ', end='')
    #     subprocess.check_call(instr, stdout=open(os.devnull, 'w'),
    #                             stderr=open(os.devnull, 'w'))
    #     print('Done.')
    # except CalledProcessError:
    #     sys.exit('[Fatal Error] Git returned a non-zero status code.')
