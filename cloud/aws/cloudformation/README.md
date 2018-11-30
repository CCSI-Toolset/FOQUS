
## PIP troposphere
pip install troposphere
pip install awacs

## Configuration File:  foqus_templates.cfg
```
[CloudInit]
admin_password = mysecretpassword
[S3]
bucket = foqus-files
```

## DynamoDB
### Create FOQUS_Resources table
```
% aws --profile ccsi dynamodb create-table --cli-input-json file://dynamodb_foqus_resources_schema.json
{
    "TableDescription": {
        "AttributeDefinitions": [
            {
                "AttributeName": "Id",
                "AttributeType": "S"
            },
            {
                "AttributeName": "Type",
                "AttributeType": "S"
            }
        ],
        "ProvisionedThroughput": {
            "NumberOfDecreasesToday": 0,
            "WriteCapacityUnits": 10,
            "ReadCapacityUnits": 10
        },
        "TableSizeBytes": 0,
        "TableName": "FOQUS_Resources",
        "TableStatus": "CREATING",
        "KeySchema": [
            {
                "KeyType": "HASH",
                "AttributeName": "Type"
            },
            {
                "KeyType": "RANGE",
                "AttributeName": "Id"
            }
        ],
        "ItemCount": 0,
        "CreationDateTime": 1542406084.306
    }
}
```
### Describe table
Use this JSON description to create a schema for a new table
```
% aws --profile ccsi dynamodb describe-table --table-name FOQUS_Resources

```
### Delete FOQUS_Resources table
```
% aws --profile ccsi dynamodb delete-table --table-name FOQUS_Resources
```
