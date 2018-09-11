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
### get-session
### get-session-list
### post-session-append
### post-session-create
### post-session-start
### get-simulation
### get-simulation-git
### get-simulation-root
### new-simulation
### delete-simulation
## Testing
```
% npm run test
```
## Deployment
```
% npm run deploy
```
