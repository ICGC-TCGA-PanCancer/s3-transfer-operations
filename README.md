## Overview

This GitHub repository is dedicated for assigning/tracking data transfer jobs
migrating PCAWG data from GNOS to Amazon S3. No software code should be added here.

For an overview of how this related to the overall S3 upload effort see the [Functional Spec](https://wiki.oicr.on.ca/display/Collabor/Functional+Spec+-+ICGC+PanCancer+Data+Load).  This repo is refered to there as the "Git Order System".

Note that all folders mentioned below are under `s3-transfer-operations` of the
current repo.

## SOP

### Major steps

* bulk generation script that queries the ES index on pancancer.info, metadata service (to get object IDs) and a project whitelist from the orchestrator (Junjun for the bulk script, Christina for project whitelist. Should start with Santa Cruz items).
   * generates JSON files in bulk and check into this GitHub repo under `backlog-jobs`
   * orchestrator examines the backlog JSON in `backlog-jobs`, moves high priority jobs to `queued-jobs`
* the Launcher VM periodically runs a script that checks out this git repo, loops over jobs in `queued-jobs`, and enqueues them into the workflow order queue system, any previously queued, running, finished, or failed are ignored
    * JSON files should be *sorted ascendingly*, files listed first are to be scheduled first
    * An MD5 sum check on the GNOS XML data should be performed prior to scheduling a workflow, when mismatch detected, no job should be scheduled and the JSON file will be moved to `failed-jobs` folder with explicit error message
* queued work on the Launcher eventually triggers the workflow to run on a Worker node, the workflow interacts with git
    * first step is to verify whether GNOS metadata XML has not been altered comparing to when the JSON file was generated. JSON is moved to `verifying-jobs`
    * running workflow moves the JSON to `downloading-jobs`
    * once download completes, JSON moved to `uploading-jobs`
    * once upload completes, JSON moved to `completed-jobs`
    * if an error is detected by the workflow JSON is moved to `failed-jobs`
    * optional: the workflow encodes debug and/or statistics in the JSON that it moves to `failed-jobs` or `completed-jobs`
* nightly, Elasticsearch index will be built picking up completed jobs from the git repo and marks relavent flags accordingly

The process above is repeated until the all JSON files (all Jobs) are moved to `completed-jobs` folder.

### Important notes

* All git operations by the workflow must be done on the `master` branch.

* Each JSON file movement should be performed as a sequence of git commands: `git checkout master && git reset --hard origin/master && git pull && git mv .... && git commit -m 'step name: json_file_name' && git push`. Replace mv .... with real json move syntax.

* The above sequence of git commands is considered to be an 'atomic' transactional operation. Failure in any of the commands will likely leave git repo in a state that could cause problems. A re-try will clear up the bad state (by removing all local changes) and hopefully get the desired git operations completed as well.

* First step in downloading phase is to download GNOS metadata XML. Before proceeding further, md5sum of this XML (after striping out the dynamic content mentioned in https://github.com/ICGC-TCGA-PanCancer/s3-transfer-operations/issues/2) must be checked against what recorded in the JSON. If md5sum does not match, transfer job must be stopped and JSON file must be moved to `failed-jobs` folder with commit message: GNOS metadata XML md5sum mismatch.

* Jobs ended up in `failed-jobs` folder should be followed up, when appropriate the corresponding JSON files need to be manually moved (git mv, commit, push) back to `queued-jobs` folder (or the `backlog-jobs`). When JSON file got stuck for unexpected duration in `downloading-jobs` or `uploading-jobs`, investigation should be carried out, when appropriate follow the process as handling failed jobs.

* No files shall be deleted in any situations!


## Example JSON file

File name: `0a76a120-80c7-4358-b495-cde8d2873c9d.BOCA-UK.CGP_donor_1635843.CGP_specimen_1704428.WGS-BWA-Normal.json`

File naming convention: `{gnos_id}.{project_code}.{donor_id}.{specimen_id}.{data_type}.json`
```
{
    "aliquot_id": "fc99c613-51bf-8b47-e040-11ac0d480d34",
    "available_repos": [
        {
            "https://gtrepo-ebi.annailabs.com/": {
                "file_md5sum": "ea6645a55aa63c8864944cb9948e0875",
                "file_size": 29513
            }
        },
        {
            "https://gtrepo-bsc.annailabs.com/": {
                "file_md5sum": "c5cb4d706bbce294e1dd5d6c347c8dde",
                "file_size": 29514
            }
        }
    ],
    "is_santa_cruz": true,
    "project_code": "BOCA-UK",
    "specimen_type": "Normal - blood derived",
    "submitter_donor_id": "CGP_donor_1635843",
    "submitter_specimen_id": "CGP_specimen_1704428",
    "submitter_sample_id": "PD12423b",
    "data_type": "WGS-BWA-Normal",
    "gnos_id": "0a76a120-80c7-4358-b495-cde8d2873c9d",
    "gnos_repo": [
        "https://gtrepo-bsc.annailabs.com/"
    ],
    "files": [
        {
            "file_md5sum": "ae3ea02c1c5d5336a67fa462bfafe908",
            "file_name": "ae3ea02c1c5d5336a67fa462bfafe908.bam",
            "file_size": 87988673853,
            "object_id": "681a7e90-3334-5c41-9808-668e821cede6"
        },
        {
            "file_md5sum": "eb9a10931adf198262de58c0d4cbb0df",
            "file_name": "ae3ea02c1c5d5336a67fa462bfafe908.bam.bai",
            "file_size": 12719888,
            "object_id": "cd46989c-0d62-5fb4-9306-06d349065b1b"
        },
        {
            "file_md5sum": "c5cb4d706bbce294e1dd5d6c347c8dde",
            "file_name": "0a76a120-80c7-4358-b495-cde8d2873c9d.xml",
            "file_size": 29514,
            "object_id": "b81d4b77-2240-5054-b217-054088f7d3f6"
        }
    ]
}
```
Fields essential to the S3 transfer job are: `gnos_id`, `gnos_repo`, `files.*`
