# Overview

This GitHub repository is dedicated for assigning/tracking data transfer jobs
migrating PCAWG data from GNOS to Amazon S3. No software code should be added here.

More details regarding the SOP come soon.

For an overview of how this related to the overall S3 upload effort see the [Functional Spec](https://wiki.oicr.on.ca/display/Collabor/Functional+Spec+-+ICGC+PanCancer+Data+Load).  This repo is refered to there as the "Git Order System".

## SOP

* bulk generation script that queries the ES index on pancancer.info and a project whitelist from the orchestrator (Junjun for the bulk script, Christina for project whitelist)
* generates JSON files in `backlog-jobs`
* orchestrator examines the backlog JSON in `backlog-jobs`, removes any entries in `"gnos_repo"` (most likely just leave a single one there for now, future workflows would support failover), moves ready jobs to `todo-jobs`
* the Launcher VM periodically runs a script that checks out this git repo, loops over jobs in `todo-jobs`, and enqueues them into the workflow order queue system, any previously queued, running, finished, or failed are ignored
* queued work on the Launcher eventually triggers the workflow to run on a Worker node, the workflow interacts with git
    * running workflow moves the JSON to `downloading-jobs`
    * once download completes, JSON moved to `uploading-jobs`
    * once upload completes, JSON moved to `completed-jobs`
    * if an error is detected by the workflow JSON is moved to `failed-jobs`
    * optional: the workflow encodes debug and/or statistics in the JSON that it moves to `failed-jobs` or `completed-jobs`

The process above is repeated until the S3 upload of the BAM files is complete.
