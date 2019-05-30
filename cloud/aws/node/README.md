# BACKEND: AWS Lambda Node.JS
## Deployment
### https://stackoverflow.com/questions/40149788/aws-api-gateway-cors-ok-for-options-fail-for-post
```
CORS For Integrated Lambda Proxy Must be done in Lambda functions
because "Integration Response" is disabled, CORS settings will not work!
```
## List of Functions
### http-basic-authorizer
HTTP BASIC Authorization using DynamoDB table for user accounts

### foqus-sns-update
listens on a FOQUS_UPDATE_TOPIC for job notifications.  These notifications
are changes of job status, results, etc.

### get-session
### get-session-list
### post-session-append
### post-session-create

### post-session-start
publishes jobs moved from 'create' to the 'submit' state to the FOQUS_JOB_TOPIC.  
Does not check DynamoDB.

### get-simulation
### get-simulation-git
### get-simulation-root
### new-simulation
### delete-simulation
### foqus-fake-job-runner
Listens on a SQS queue for job submissions and moves them to a 'success' state
by publishing updates to the FOQUS_UPDATE_TOPIC.

## Testing
```
% npm install
% npm run test
```
## Deployment
```
% npm run deploy
```
