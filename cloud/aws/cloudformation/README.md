
## python dependencies
```
pip install troposphere
pip install awacs
```

## configuration file: foqus_templates.cfg
Change bucket name to one in your account that you have access to.
```
[S3]
bucket = foqus-files
```
## CloudFormation
### Layer 1:  FOQUS_Cloud_VPC_Main_template.json 
Create a VPC, public subnet, EIN, EIP, SecurtiyGroup, etc
#### Output:
```
'vpc-033ea6ef05b915965' 
'subnet-053ea9ce59266c6a7' 
'igw-0be217e2c34ea807b' 
'eni-03c1257c37edddd26' 
'eipalloc-090b3060613bf7d24'
```
### Layer 2:  SLM Server
```
% python FOQUS_SLM_instance_in_subnet.py 'vpc-033ea6ef05b915965' 'subnet-053ea9ce59266c6a7' 'igw-0be217e2c34ea807b' 'eni-03c1257c37edddd26' 'eipalloc-090b3060613bf7d24' > FOQUS_SLM_instance_in_subnet.json
```
