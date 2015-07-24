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

* Each JSON file movement should be performed as a sequence of git commands: `git checkout master && git reset --hard origin/master && git fetch --all && git mv .... && git commit -m 'step name: json_file_name' && git push`. Replace mv .... with real json move syntax.

* The above sequence of git commands is considered to be an 'atomic' transactional operation. Failure in any of the commands will likely leave git repo in a state that could cause problems. A re-try will clear up the bad state (by removing all local changes) and hopefully get the desired git operations completed as well.

* First step in downloading phase is to download GNOS metadata XML. Before proceeding further, md5sum of this XML (after striping out the dynamic content mentioned in https://github.com/ICGC-TCGA-PanCancer/s3-transfer-operations/issues/2) must be checked against what recorded in the JSON. If md5sum does not match, transfer job must be stopped and JSON file must be moved to `failed-jobs` folder with commit message: GNOS metadata XML md5sum mismatch.

* Jobs ended up in `failed-jobs` folder should be followed up, when appropriate the corresponding JSON files need to be manually moved (git mv, commit, push) back to `queued-jobs` folder (or the `backlog-jobs`). When JSON file got stuck for unexpected duration in `downloading-jobs` or `uploading-jobs`, investigation should be carried out, when appropriate follow the process as handling failed jobs.

* No files shall be deleted in any situations!


## Example JSON file

File name: `54beeb57-e18e-49de-a49b-b8dc2ac91088.PACA-CA.PCSI_0235.PCSI_0235_Ly_R.WGS-BWA-Normal.json`

File naming convention: `{gnos_id}.{project_code}.{donor_id}.{specimen_id}.{data_type}.json`
```
{
    "available_repos": [
        "https://gtrepo-ebi.annailabs.com/",
        "https://gtrepo-bsc.annailabs.com/"
    ],
    "is_santa_cruz": false,
    "project_code": "PACA-CA",
    "submitter_donor_id": "PCSI_0235",
    "submitter_specimen_id": "PCSI_0235_Ly_R",
    "submitter_sample_id": "PCSI_0235_Ly_R",
    "aliquot_id": "7d752281-be08-47c9-ad83-dfcf2347ba5e",
    "specimen_type": "Normal - blood derived",
    "data_type": "WGS-BWA-Normal",
    "gnos_id": "54beeb57-e18e-49de-a49b-b8dc2ac91088",
    "gnos_repo": [
        "https://gtrepo-bsc.annailabs.com/"
    ],
    "files": [
        {
            "file_md5sum": "fdac6eb702b99c391c092e25c35ea594",
            "file_name": "fdac6eb702b99c391c092e25c35ea594.bam",
            "file_size": 114968925237,
            "object_id": "936440a1-1679-4401-9963-a6e75315d55d"
        },
        {
            "file_md5sum": "c16bedaff311ef8b4c311d9661d030ec",
            "file_name": "fdac6eb702b99c391c092e25c35ea594.bam.bai",
            "file_size": 14741520,
            "object_id": "6e637cd9-de95-4d8f-9a45-776f7e39ff9e"
        },
        {
            "file_md5sum": "52ec96b4298843efb05462989676cd37",
            "file_name": "54beeb57-e18e-49de-a49b-b8dc2ac91088.xml",
            "file_size": 31573,
            "object_id": "537088ac-36c0-4387-b204-12cc473ec7c4"
        }
    ]
}
```
Fields essential to the S3 transfer job are: `gnos_id`, `gnos_repo`, `files.*`
