# FOQUS Cloud

## Worker
### AWS SQS, SNS, DynamoDB, S3
The python module `foqus_service.py` is runnable as a Windows Service.  The service will
periodically check an AWS SQS job submission queue for job requests.  Once one is available
the item is temporarily `locked` while the job is setup.  If the job is successfully setup or
an error occurs, the item is deleted from the queue.  So if the worker is unexpectedly
shutdown the job will automatically appear back on the queue after a VisibilityTimeout.

All state transitions are published to the SNS Update Topic and foqus_update_topic lambda function performs the actual updates and writes.  DynamoDB and S3 access is READ-Only for the worker.

Kill requests are communicated through the DynamoDB table entry for the job request.

## Web Resources and Lambda Functions
There are two main web resources the `Session` and the `Simulation`.  `Session` is a logical grouping of job requests, and the `Simulation` is a logical grouping of staged files and an execution engine (ACM, AspenPlus, etc).

### Session Resource
#### get-session
##### AWS DynamoDB
Query for all Job's with session_id, expired jobs (TTL) will not be present.

#### get-session-list
##### AWS S3
List all keys in bucket under prefix `s3://{bucket_name}/{user_name}/{session_id}/``

#### get-session-result
##### AWS S3
Get the object `s3://{bucket_name}/{user_name}/session/{session_id}/page/number/{page_number}.json` and returns to calling party.

#### post-session-append
##### AWS DynamoDB and S3
Write job items to DynamoDB Table, put job array in S3 key

`s3://{bucket_name}/{user_name}/{session_id}/{milliseconds_since_epoch}.json`

### post-session-create
Return a new UUID that can be used for a new session.

### post-session-kill
#### AWS SNS
Publishes a session kill event to `FOQUS_UPDATE_TOPIC`.  This will prevent any new jobs in this session from running, and request workers to terminate currently running jobs in the session.  These jobs will be moved to status `terminate`.

### post-session-result
#### AWS S3
Lists grabs all keys under `s3://{bucket_name}/{user_name}/session/{session_id}/`.

The algorithm uses

1. `s3://{bucket_name}/{user_name}/session/{session_id}/finished/{milliseconds_since_epoch}/{state}/{job_id}.json`.
2. `s3://{bucket_name}/{user_name}/session/{session_id}/page/milliseconds/{milliseconds_since_epoch}.json`.
3. `s3://{bucket_name}/{user_name}/session/{session_id}/page/number/{page_number}.json`

Count how many pages are under `{session_id}/page/milliseconds/` to determine the next page number and largest `{milliseconds_since_epoch}`, which represents the finish time of the most recent job included in a page.  Unfortunately this algorithm will break down if there is skew in a clock.  

Next iterate through all finished jobs and select only those whose `finish` times exceed the `{milliseconds_since_epoch}` from above.  All these jobs will be saved to a JSON array in the next page number (key types 2 and 3), the `page_number` will be returned to the calling party.


### post-session-start
##### AWS S3 and SNS
Lists all keys with prefix `s3://{bucket_name}/{user_name}/{session_id}/`, gets each JSON array and publishes each as event `job.submit` to SNS FOQUS_UPDATE_TOPIC. This topic is configured to publish to both the lambda function `foqus_update_topic` and the SQS job queue.

### Simulation Resource
#### get-simulation-input-file
#### get-simulation-list
#### post-simulation-signed-url
#### put-simulation-input
#### put-simulation-name

### Other
#### http-basic-authorizer
HTTP BASIC Authorization using DynamoDB table for user accounts
#### foqus-sns-update
Listens on the `FOQUS_UPDATE_TOPIC` for notifications concerning jobs, workers, sessions.  These notifications are state changes.  Most of the `post-session*` lambda functions send processing requests to this TOPIC.
### foqus-fake-job-runner
Listens on a SQS queue for job submissions and moves them to a 'success' state by publishing updates to the `FOQUS_UPDATE_TOPIC` .

### Deployment Notes
#### https://stackoverflow.com/questions/40149788/aws-api-gateway-cors-ok-for-options-fail-for-post
```
CORS For Integrated Lambda Proxy Must be done in Lambda functions
because "Integration Response" is disabled, CORS settings will not work!
```

## Testing
```
% npm install
% npm run test
```
## Deployment
```
% npm run deploy
```
