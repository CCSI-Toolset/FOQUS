#################################################################################
# FOQUS Copyright (c) 2012 - 2024, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
import json, os, copy
import boto3
import numpy as np
from sdoe import usf
from botocore.exceptions import ClientError

CONSUMER_ID = "00000000-0000-0000-0000-000000000000"


def lambda_handler(event, context):
    # SLM Security Group us-east-1 sg-097636e72d37d985f
    # ec2 = boto3.client('ec2', region_name='us-east-1')
    print("EVENT: %s" % (json.dumps(event)))
    s3 = boto3.client("s3")
    sns = boto3.client("sns")
    update_topic_arn = os.environ["FOQUS_Update_Topic_Arn"]
    print("TOPIC_ARN: %s" % (update_topic_arn))

    num_executions = 0
    assert "Records" in event, "Format Error: No Records in SNS Message"

    for record in event["Records"]:
        msg_id = record["messageId"]
        body = record["body"]
        job = json.loads(body)
        if job["resource"] != "job":
            print("ERROR Misconfigured -- IGNORE Resource: %s" % (job))
            continue
        if job["event"] != "status" or job["status"] != "submit":
            print("ERROR Misconfigured -- IGNORE JOB: %s" % (job))
            continue

        application = record["messageAttributes"]["application"]["stringValue"]
        job_id = record["messageAttributes"]["job"]["stringValue"]
        session_id = record["messageAttributes"]["session"]["stringValue"]
        username = record["messageAttributes"]["username"]["stringValue"]
        # simulation = record['messageAttributes']['simulation']['stringValue']
        assert application.startswith("sdoe")
        # assert simulation.startswith('sdoe')
        msg_attrs = dict()
        msg_attrs["application"] = dict(StringValue=application, DataType="String")
        msg_attrs["event"] = dict(StringValue="job.setup", DataType="String")
        msg_attrs["job"] = dict(StringValue=job_id, DataType="String")
        msg_attrs["session"] = dict(StringValue=session_id, DataType="String")
        msg_attrs["username"] = dict(StringValue=username, DataType="String")
        """
        "body": "{\"Initialize\":false,\"Input\":{},\"Reset\":false,\"Application\":\"sdoe.usf.compute_min_dist\",
        \"Simulation\":\"sdoe.usf.compute_min_dist\",\"Visible\":false,\"Id\":\"be84bcdb-a682-4d97-805b-e5e4748df7ce\",
        \"resource\":\"job\",\"status\":\"submit\",\"jobid\":\"be84bcdb-a682-4d97-805b-e5e4748df7ce\",
        \"sessionid\":\"e59589d3-4e77-48e3-b946-c2abac8d8e0e\",
        \"event\":\"status\"}",
        """
        job2 = copy.deepcopy(job)
        job2["consumer"] = CONSUMER_ID
        job2["instanceid"] = "lambda"
        job2["status"] = "setup"
        params = dict(
            Message=json.dumps(job2),
            MessageAttributes=msg_attrs,
            TopicArn=update_topic_arn,
        )
        ret = sns.publish(**params)

        msg_attrs["event"]["StringValue"] = "job.running"
        job2["status"] = "running"
        params = dict(
            Message=json.dumps(job2),
            MessageAttributes=msg_attrs,
            TopicArn=update_topic_arn,
        )
        ret = sns.publish(**params)

        input = job["Input"]
        mat = input.get("mat")
        scl = input.get("scl")
        """ [[1, 1], [2, 2], [3, 3]]
            [2.0, 2.0]
        """
        try:
            mat = np.array(mat)
            scl = np.array(scl)
        except Exception as e:
            print("ERROR packing numpy arrays")
            msg_attrs["event"]["StringValue"] = "job.error"
            job2["event"] = "status"
            job2["status"] = "error"
            job2["message"] = "ERROR packing numpy arrays: %s" % (e)
            params = dict(
                Message=json.dumps(job2),
                MessageAttributes=msg_attrs,
                TopicArn=update_topic_arn,
            )
            ret = sns.publish(**params)
            return {"statusCode": 400, "body": json.dumps(dict(error=str(e)))}
        try:
            dmat, min_dist = usf.compute_min_dist(mat, scl, hist_xs=None)
            # assert np.array_equal(
            #     np.array([[10.0, 0.5, 2.0], [0.5, 10.0, 0.5], [2.0, 0.5, 10.0]]), dmat
            # )
            # assert np.array_equal(np.array([0.5, 0.5, 0.5]), min_dist)
        except Exception as e:
            print("ERROR Calling compute_min_dist")
            msg_attrs["event"]["StringValue"] = "job.error"
            job2["event"] = "status"
            job2["status"] = "error"
            job2["message"] = "ERROR Calling compute_min_dist: %s" % (e)
            params = dict(
                Message=json.dumps(job2),
                MessageAttributes=msg_attrs,
                TopicArn=update_topic_arn,
            )
            ret = sns.publish(**params)
            return {"statusCode": 400, "body": json.dumps(dict(error=str(e)))}

        msg_attrs["event"]["StringValue"] = "job.output"
        job2["event"] = "output"
        job2["value"] = json.dumps(dict(dmat=dmat.tolist(), min_dist=min_dist.tolist()))
        params = dict(
            Message=json.dumps(job2),
            MessageAttributes=msg_attrs,
            TopicArn=update_topic_arn,
        )
        ret = sns.publish(**params)

        msg_attrs["event"]["StringValue"] = "job.success"
        job2["event"] = "status"
        job2["status"] = "success"
        params = dict(
            Message=json.dumps(job2),
            MessageAttributes=msg_attrs,
            TopicArn=update_topic_arn,
        )
        ret = sns.publish(**params)
        num_executions += 1

    print("Finished: SDOE Executions %d" % (num_executions))
    return {"statusCode": 200, "body": "SDOE Executions %d" % (num_executions)}


def test_handler(event, context):
    # SLM Security Group us-east-1 sg-097636e72d37d985f
    # ec2 = boto3.client('ec2', region_name='us-east-1')
    s3 = boto3.client("s3")
    sqs = boto3.client("sqs")
    try:
        print("START")
        rsp = s3.list_buckets()
        buckets = map(lambda i: i["Name"], rsp["Buckets"])
        print("RESPONSE: %s", str(list(buckets)))
    except ClientError as e:
        print(e)
        return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}
    return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}
