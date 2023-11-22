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

### Backend: Node.js Lambda Functions (node v12)
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
### FOQUS Worker Image Setup
#### Install FOQUS
Open an Anaconda3 terminal and install base packages.
```
(base) C:\Users\Administrator\Desktop> conda activate foqus
(foqus) C:\Users\Administrator\Desktop> conda install git
(foqus) C:\Users\Administrator\Desktop> conda install -c conda-forge nlopt
(foqus) C:\Users\Administrator\Desktop> python -m pip install --upgrade pip
(foqus) C:\Users\Administrator\Desktop> pip install git+https://github.com/CCSI-Toolset/foqus@master
```
##### (OPTIONAL) Run FOQUS tests
```
(foqus) C:\Users\Administrator\Desktop> git clone https://github.com/CCSI-Toolset/foqus; cd FOQUS
(foqus) C:\Users\Administrator\Desktop\FOQUS> pip install -r requirements.txt
(foqus) C:\Users\Administrator\Desktop\FOQUS> pytest
================================================= test session starts =================================================
platform win32 -- Python 3.7.3, pytest-5.1.2, py-1.8.0, pluggy-0.13.0
rootdir: C:\Users\Administrator\Desktop\FOQUS, inifile: pytest.ini, testpaths: foqus_lib
collected 5 items

foqus_lib\framework\sampleResults\test\results_s3_test.py .....                                                  [100%]

================================================== 5 passed in 2.44s ==================================================
```
#### Install TurbineLite and dependencies
1. Install [SQL Compact 4.0 x64](https://www.microsoft.com/en-us/download/details.aspx?id=17876)
2. Install [SimSinterInstaller.msi](https://github.com/CCSI-Toolset/SimSinter/releases/download/2.0.0/SimSinterInstaller.msi)
3. Install [TurbineLite.msi](https://github.com/CCSI-Toolset/turb_sci_gate/releases/download/2.0.0/TurbineLite.msi)
4. Install AspenTech v10
```
After installing Aspen you will need to configure the license server
Next run AspenTech/ACM and decline to register the product (otherwise it will hang indefinitely).
```
#### Install FOQUS Windows Service
```
(foqus) C:\Users\Administrator\Desktop\FOQUS\cloud\aws>python foqus_service.py
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

(foqus) C:\Users\Administrator\Desktop\FOQUS\cloud\aws> python foqus_service.py  --startup delayed --interactive install
Installing service FOQUS-Cloud-Service
Service installed

(base) C:\Users\Administrator>
```
#### Update Windows PATH with Anaconda dependencies
#### Print Current PATH
```
(foqus) C:\Users\Administrator\Desktop\FOQUS\cloud\aws>echo %PATH%
C:\tools\Anaconda3\envs\foqus;C:\tools\Anaconda3\envs\foqus\Library\mingw-w64\bin;C:\tools\Anaconda3\envs\foqus\Library\usr\bin;C:\tools\Anaconda3\envs\foqus\Library\bin;C:\tools\Anaconda3\envs\foqus\Scripts;C:\tools\Anaconda3\envs\foqus\bin;C:\tools\Anaconda3\condabin;C:\Program Files\Microsoft MPI\Bin;C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Program Files (x86)\Microsoft SQL Server\130\Tools\Binn;C:\Program Files\Microsoft SQL Server\130\Tools\Binn;C:\Program Files (x86)\Microsoft SQL Server\130\DTS\Binn;C:\Program Files\Microsoft SQL Server\130\DTS\Binn;C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn;C:\Program Files (x86)\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn;C:\Program Files (x86)\Microsoft SQL Server\130\Tools\Binn\ManagementStudio;C:\Program Files\Amazon\cfn-bootstrap;C:\ProgramData\chocolatey\bin;.;C:\Program Files (x86)\Common Files\Intel\Shared Libraries\redist\intel64_win\compiler;C:\Program Files (x86)\Common Files\AspenTech Shared;C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps;C:\Program Files\Common Files\AspenTech Shared
```
1.  Powershell Method
Open a powershell terminal and copy the path from above to set the machine system PATH environment variable to allow the `foqus_service.py` to run as a Windows Service.
```
PS C:\Users\Administrator\Desktop> $P1 = "C:\ProgramData\Anaconda3\envs\foqus;C:\ProgramData\Anaconda3\envs\foqus\Library\mingw-w64\bin;C:\ProgramData\Anaconda3\envs\foqus\Library\usr\bin;C:\ProgramData\Anaconda3\envs\foqus\Library\bin;C:\ProgramData\Anaconda3\envs\foqus\Scripts;C:\ProgramData\Anaconda3\envs\foqus\bin;C:\ProgramData\Anaconda3\condabin;C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Program Files\Amazon\cfn-bootstrap;C:\Program Files (x86)\Microsoft SQL Server\110\Tools\Binn;C:\Program Files\Microsoft SQL Server\110\Tools\Binn;C:\Program Files\Microsoft SQL Server\110\DTS\Binn;C:\Program Files (x86)\Common Files\AspenTech Shared"

PS C:\Users\Administrator\Desktop> $P1 =
"C:\tools\Anaconda3\envs\foqus;C:\tools\Anaconda3\envs\foqus\Library\mingw-w64\bin;C:\tools\Anaconda3\envs\foqus\Library\usr\bin;C:\tools\Anaconda3\envs\foqus\Library\bin;C:\tools\Anaconda3\envs\foqus\Scripts;C:\tools\Anaconda3\envs\foqus\bin;C:\tools\Anaconda3\envs\foqus\condabin"

$P2 = "C:\tools\Anaconda3;C:\tools\Anaconda3\Library\mingw-w64\bin;C:\tools\Anaconda3\Library\usr\bin;C:\tools\Anaconda3\Library\bin;C:\tools\Anaconda3\Scripts;C:\tools\Anaconda3\bin;C:\tools\Anaconda3\condabin"


$P3 = "C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Program Files\Amazon\cfn-bootstrap;C:\ProgramData\chocolatey\bin;C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps"

[Environment]::SetEnvironmentVariable('path', "$P1;$P2;$P3", 'Machine');
```
Second, add several Anaconda3 Library paths.
```
PS C:\Users\Administrator\Desktop> $P2 = "$P1;C:\ProgramData\Anaconda3\Library\bin;C:\ProgramData\Anaconda3\DLLs;C:\ProgramData\Anaconda3\lib;C:\ProgramData\Anaconda3;C:\ProgramData\Anaconda3\lib\site-packages;C:\ProgramData\Anaconda3\lib\site-packages\win32;C:\ProgramData\Anaconda3\lib\site-packages\win32\lib;C:\ProgramData\Anaconda3\lib\site-packages\Pythonwin"

PS C:\Users\Administrator\Desktop> [Environment]::SetEnvironmentVariable('path', "$P2", 'Machine');
```
2.  Control Panel Method
```
Append the path above in method1 ( $P2 ) by navigating to the control panel:
control panel/system and security/system/advanced system settings/environment variables/PATH
```
#### Windows 2012/2016 NoInteractiveServices Registry
##### EventViewer Errors
In newer versions of Windows the `Service Control Manager` will error when starting because by default this Registry property is turned-on by default.
```
The FOQUS Cloud Service service is marked as an interactive service.  However, the system is configured to not allow interactive services.  This service may not function properly.
```
##### Registry get NoInteractiveServices
```
PS C:\Users\Administrator> Get-ItemProperty -path HKLM:\SYSTEM\CurrentControlSet\Control\Windows\ -Name NoInteractiveServices

NoInteractiveServices : 1
PSPath                : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Windows
                        \
PSParentPath          : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control
PSChildName           : Windows
PSDrive               : HKLM
PSProvider            : Microsoft.PowerShell.Core\Registry
PS C:\Users\Administrator> Set-ItemProperty -path HKLM:\SYSTEM\CurrentControlSet\Control\Windows\ -Name NoInteractiveServices -Value 0
```
##### Registry set NoInteractiveServices
```
PS C:\Users\Administrator> Set-ItemProperty -path HKLM:\SYSTEM\CurrentControlSet\Control\Windows\ -Name NoInteractiveServices -Value 0
PS C:\Users\Administrator> Get-ItemProperty -path HKLM:\SYSTEM\CurrentControlSet\Control\Windows\ -Name NoInteractiveServices

NoInteractiveServices : 0
PSPath                : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Windows
                        \
PSParentPath          : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control
PSChildName           : Windows
PSDrive               : HKLM
PSProvider            : Microsoft.PowerShell.Core\Registry
```

### FOQUS Worker VM Configuration
After installing and configuring required software above the instance can be imaged,
and then the AMI can be used to create instances (VMs), and the User-Data is the means
of configuring the FOQUS Service.  It is expected to be a JSON Object like below.
```
PS C:\Users\Administrator> $rsp = Invoke-RestMethod -Uri $URL
PS C:\Users\Administrator> $rsp | ConvertTo-Json
{
    "FOQUS-Update-Topic-Arn":  "arn:aws:sns:us-west-2:387057575688:FoqusCloudStack-bluejobtopicidA63AF7BE-NY5APVGJL24B",
    "FOQUS-Message-Topic-Arn":  "arn:aws:sns:us-west-2:387057575688:FoqusCloudStack-bluelogtopicid50E21335-PBVQAP0RYZ5D",
    "FOQUS-Job-Queue-Url":  "arn:aws:sqs:us-west-2:387057575688:FoqusCloudUserStack-blueboverhofqueueidEDBC6161-zgo4wkNousqm",
    "FOQUS-Simulation-Bucket-Name":  "arn:aws:s3:::foquscloudstack-bluefoqussimulation99ec6532-170r4pwindi5n"
}
PS C:\Users\Administrator> echo $URL
http://169.254.169.254/latest/user-data
```
## Testing

## Reference: AWS Resources
### SQS
```
FOQUS-Job-Queue
FOQUS-Update-Queue
```
### SNS Topics
```
FOQUS-Job-Topic
FOQUS-Update-Topic
```
### EC2
```
AMI
```
### API Gateway
```
Turbine Gateway API2
```
### Lambda
```
http-basic-authorizer-[stage]
post-session-start-[stage]
post-session-create-[stage]
post-session-append-[stage]
get-session-list[stage]
get-session-[stage]
get-simulation-root-[stage]
get-simulation-[stage]
```
### S3 Buckets
```
foqus-sessions
foqus-simulations
```
### DynamoDB Tables
```
TurbineUsers
FOQUS_Resources
```
