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
#### Install TurbineLite and dependencies
1. Install [SQL Compact 4.0 x64](https://www.microsoft.com/en-us/download/details.aspx?id=17876) 
2. Install [SimSinterInstaller.msi](https://github.com/CCSI-Toolset/SimSinter/releases/download/2.0.0/SimSinterInstaller.msi) 
3. Install [TurbineLite.msi](https://github.com/CCSI-Toolset/turb_sci_gate/releases/download/2.0.0/TurbineLite.msi)

#### Install FOQUS Windows Service
```
(base) C:\Users\Administrator>python \ProgramData\Anaconda2\Scripts\foqus_service.py
Usage: 'foqus_service.py [options] install|update|remove|start [...]|stop|restart [...]|debug [...]'
Options for 'install' and 'update' commands only:
 --username domain\username : The Username the service is to run under
 --password password : The password for the username
 --startup [manual|auto|disabled|delayed] : How the service starts, default = manual
 --interactive : Allow the service to interact with the desktop.
 --perfmonini file: .ini file to use for registering performance monitor data
 --perfmondll file: .dll file to use when querying the service for
   performance data, default = perfmondata.dll
Options for 'start' and 'stop' commands only:
 --wait seconds: Wait for the service to actually start or stop.
                 If you specify --wait with the 'stop' option, the service
                 and all dependent services will be stopped, each waiting
                 the specified period.

(base) C:\Users\Administrator>python \ProgramData\Anaconda2\Scripts\foqus_service.py  --startup delayed --interactive install
Installing service FOQUS-Cloud-Service
Service installed

(base) C:\Users\Administrator>
```
#### Update Windows PATH with Anaconda dependencies
1.  Powershell Method1: Unfortunately this doesn't work because it's truncated
```
PS C:\Users\Administrator> setx /M PATH "$($env:path);C:\ProgramData\Anaconda2\python27.zip;C:\ProgramData\Anaconda2\DLLs;C:\ProgramData\Anaconda2\lib;C:\ProgramData\Anaconda2\lib\plat-win;C:\ProgramData\Anaconda2\lib\lib-tk;C:\ProgramData\Anaconda2;C:\ProgramData\Anaconda2\lib\site-packages;C:\ProgramData\Anaconda2\lib\site-packages\Babel-2.5.0-py2.7.egg;C:\ProgramData\Anaconda2\lib\site-packages\win32;C:\ProgramData\Anaconda2\lib\site-packages\win32\lib;C:\ProgramData\Anaconda2\lib\site-packages\Pythonwin"

WARNING: The data being saved is truncated to 1024 characters.

SUCCESS: Specified value was saved.
```

## Testing
