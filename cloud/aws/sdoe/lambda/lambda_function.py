import json
import boto3
import numpy as np
from sdoe import usf
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # SLM Security Group us-east-1 sg-097636e72d37d985f
    #ec2 = boto3.client('ec2', region_name='us-east-1')
    s3 = boto3.client('s3')
    sqs = boto3.client('sqs')
    try:
        mat = np.array([[1, 1], [2, 2], [3, 3]])
        scl = np.array([2.0, 2.0])
        dmat, min_dist = usf.compute_min_dist(mat, scl, hist_xs=None)
        assert np.array_equal(
            np.array([[10.0, 0.5, 2.0], [0.5, 10.0, 0.5], [2.0, 0.5, 10.0]]), dmat
        )
        assert np.array_equal(np.array([0.5, 0.5, 0.5]), min_dist)
    except Exception as e:
        print(e)
        return {
            'statusCode': 200,
            'body': json.dumps(dict(error=str(e)))
        }
    return {
        'statusCode': 200,
        'body': json.dumps(dict(dmat=dmat.tolist(), min_dist=min_dist.tolist()))
    }

def test_handler(event, context):
    # SLM Security Group us-east-1 sg-097636e72d37d985f
    #ec2 = boto3.client('ec2', region_name='us-east-1')
    s3 = boto3.client('s3')
    sqs = boto3.client('sqs')
    try:
        print("START")
        rsp = s3.list_buckets()
        buckets = map(lambda i: i['Name'], rsp['Buckets'])
        print("RESPONSE: %s", str(list(buckets)))
    except ClientError as e:
        print(e)
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!')
        }
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
