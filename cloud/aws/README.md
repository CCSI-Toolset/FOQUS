# FOQUS AWS Cloud

##  Architecture Overview
### Web Services API Frontend
AWS API Gateway specifies Web Service interface, and hooks into AWS Lambda Backend where all processesing takes place.
AWS S3 is used for file storage, which includes sessions and simulations.
AWS DynamoDB is used for job and consumer status tracking, and user management.

#### Session Resource
##### GET session
-- returns JSON array of all sessions
##### POST session
-- return session UUID
##### GET session/{id}
-- returns JSON array of all "metadata" for jobs in session
##### POST session/{id}/start
-- sends all jobs in session to submit queue
##### POST session/{id}
-- sends all jobs in session to submit queue

### Backend: Node.js Lambda Functions (node v6.1.0)
Processes API Requests and Notifications from the EC2 FOQUS Workers
#### Web Services API Backend
#### Worker Notification Processor

### FOQUS Workers: EC2 VMs
Process FOQUS job queue (AWS SQS) requests, generate notifications of status changes (AWS SNS) and upload generated files to various Amazon S3 Buckets.

## Management
### User Credentials
Currently store user/password information in DynamoDB FOQUSUsers table.  To create a user add a row.

## Monitoring
### CloudWatch

## Deployment
### FOQUS Worker
#### Install FOQUS
Open an Anaconda-5.0.* terminal and install base packages.
```
% conda install git
% python -m pip install --upgrade pip
% pip install git+https://github.com/CCSI-Toolset/turb_client@master
% pip install git+https://github.com/CCSI-Toolset/foqus@master
```
#### Install TurbineLite
1. Install SQL Compact 4.0 x64 ( MUST INSTALL 64 bit on x64 platform )
2. Install SimSinterInstaller.msi
3. Install TurbineLite.msi

#### Install FOQUS Windows Service
```
% python foqus_service.py install
```

## Testing
