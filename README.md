## Overview

This GitHub repository is dedicated for assigning/tracking data transfer jobs
migrating PCAWG data from GNOS to Amazon S3. No software code should be added here.

For an overview of how this related to the overall S3 upload effort see the [Functional Spec](https://wiki.oicr.on.ca/display/Collabor/Functional+Spec+-+ICGC+PanCancer+Data+Load).  This repo is refered to there as the "Git Order System".

Note that all folders mentioned below are under `s3-transfer-operations` of the
current repo.

## SOP

* bulk generation script that queries the ES index on pancancer.info, metadata service (to get object IDs) and a project whitelist from the orchestrator (Junjun for the bulk script, Christina for project whitelist. Should start with Santa Cruz items).
   * generates JSON files in bulk and check into this GitHub repo under `backlog-jobs`
   * orchestrator examines the backlog JSON in `backlog-jobs`, moves high priority jobs to `todo-jobs`
* the Launcher VM periodically runs a script that checks out this git repo, loops over jobs in `todo-jobs`, and enqueues them into the workflow order queue system, any previously queued, running, finished, or failed are ignored
    * JSON files should be sorted ascendingly, files listed first are to be scheduled first
* queued work on the Launcher eventually triggers the workflow to run on a Worker node, the workflow interacts with git
    * running workflow moves the JSON to `downloading-jobs` followed by git commit and push
    * once download completes, JSON moved to `uploading-jobs` followed by git commit and push 
    * once upload completes, JSON moved to `completed-jobs` followed by git commit and push
    * if an error is detected by the workflow JSON is moved to `failed-jobs` followed by git commit and push
    * optional: the workflow encodes debug and/or statistics in the JSON that it moves to `failed-jobs` or `completed-jobs`

The process above is repeated until the all JSON files (all Jobs) are moved to `completed-jobs` folder


## Example JSON file

File name: `a0001.PACA-CA.38a2dbee-063a-401e-8d4c-fdd1116d91fb.BAW-Normal.json`

File naming convention: `{prefix_for_priority}.{project_code}.{gnos_id}.{data_type}.json`
```
{
   "data_type": "bwa_alignment",
   "project_code": "PACA-CA",
   "submitter_donor_id": "PCSI_0451",
   "is_santa_cruz": true,
   "specimen_type": "Normal - other", 
   "submitter_sample_id": "ASHPC_0023_Pa_R", 
   "submitter_specimen_id": "ASHPC_0023_Pa_R",
   "aliquot_id": "72a3ad80-9722-49bb-b508-c88b48dfd0bb", 
   "gnos_id": "38a2dbee-063a-401e-8d4c-fdd1116d91fb", 
   "gnos_repo": [
       "https://gtrepo-bsc.annailabs.com/"
   ], 
   "files": [
       {
           "file_name": "38a2dbee-063a-401e-8d4c-fdd1116d91fb.xml",
           "file_md5sum": "dd990adba7b83a457ee69a879699ef06",
           "file_size": 19650,
           "object_id": "63269040-ed8e-4efb-8fd4-220aac448171"
       },
       {
           "file_name": "61a67b41ed8dbe7bc4c32625dfe74814.bam", 
           "file_md5sum": "61a67b41ed8dbe7bc4c32625dfe74814", 
           "file_size": 169999662650,
           "object_id": "63269040-ed8e-4efb-8fd4-220aac448172"
       },
       {
           "file_name": "61a67b41ed8dbe7bc4c32625dfe74814.bam.bai", 
           "file_md5sum": "50b5a2ae835a180cafb6e386cfd87a97",
           "file_size": 3516116,
           "object_id": "5f0db67d-5a46-422e-8b57-48ce79165ff6"
       }
   ] 
}
```
