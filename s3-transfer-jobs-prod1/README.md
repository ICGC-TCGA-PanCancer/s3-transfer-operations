Important Note
=====

This folder and all sub-folders are meant for production use. Other than adding new JSON files
to `backlog-jobs` and enqueuing jobs by moving JSON files from `backlog` to `queued-jobs` folder,
JSON file movement in these folders: `verifying-jobs`, `downloading-jobs`, `uploading-jobs`, 
`failed-jobs` and `completed-jobs` should only be performed by workflow process. Manual manipulation of files
in these folders may result in workflow abnormal termination! One exception is that when it is verified
that a job has already failed and the corresponding JSON file got stuck in one of the middle folders,
it would be necessary to manually move this file back to `backlog-jobs` or `queued-jobs` depending on
the situation.
