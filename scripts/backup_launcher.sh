#!/usr/bin/env bash

set -e

s3_url_db_backup='s3://oicr.icgc-backups/s3-transfers/db_dumps/prod1'
temp_dir=`mktemp -d`
output_file=launcher_${3:-prod1}_`date +%Y-%m-%dT%H-%M-%S%z`.sql

pg_dump -U ${1:-queue_user} ${2:-queue_status} > $temp_dir/$output_file

aws s3 cp $temp_dir/$output_file $s3_url_db_backup > /dev/null 2>&1

echo "Backed-up database ${2:-queue_status} and uploaded to $s3_url_db_backup/$output_file."
