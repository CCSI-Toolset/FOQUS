/**
 * Lambda Function
 *
 * @module status
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 */
const AWS = require('aws-sdk');
const log = require("debug")("status")
const dynamodb = new AWS.DynamoDB.DocumentClient({ apiVersion: '2012-08-10', region: process.env.AWS_REGION });
const ec2 = new AWS.EC2({apiVersion: '2016-11-15'});
const autoscaling = new AWS.AutoScaling({apiVersion: '2011-01-01'});
const sqs = new AWS.SQS({apiVersion: '2012-11-05'});

const TABLE_NAME = process.env.FOQUS_WEBSOCKET_TABLE_NAME;
const FOQUS_JOB_QUEUE = process.env.FOQUS_JOB_QUEUE;
//const API_GATEWAY_ENDPOINT = process.env.FOQUS_WEBSOCKET_API_GATEWAY_ENDPOINT


exports.handler = async event => {
  log("request: " + JSON.stringify(event));
  let connectionData;
  let instanceData;
  let autoscaleData;
  let queueUrl;
  let queueData;
  let statusData;
  let response;
  //const connectionId = event.requestContext.connectionId;
  // DynamoDB
  //params = {
  //    TableName: TABLE_NAME,
  //    Key: {"Id": connectionId, "Type":"WebSocket"}
  //};
  var params = {
      TableName: TABLE_NAME,
      KeyConditionExpression: '#T = :websocket',
      ExpressionAttributeNames: {"#T":"Type"},
      ExpressionAttributeValues: { ":websocket":"WebSocket"}
  };
  try {
    connectionData = await dynamodb.query(params).promise();
  } catch (e) {
    log("ERROR", e.stack);
    return { statusCode: 500, body: e.stack };
  }
  log("connectionData: " + JSON.stringify(connectionData));
  const userName = connectionData.Username;
  // autoscaling
  params = {
   AutoScalingGroupNames: [
      "FOQUS_Workers_AutoScale_v1"
   ]
  };
  try {
    autoscaleData = await autoscaling.describeAutoScalingGroups(params).promise();
  } catch (e) {
    log("Failed to get autoscaleData: ", e.stack);
    //return { statusCode: 500, body: e.stack };
    autoscaleData = {}
  }
  //log("autoscaleData: " + JSON.stringify(autoscaleData));

  // EC2
  params = {
    Filters : [
      {
        Name: "tag:Deployment",
        Values: ["FOQUS"]
      }
    ]
  };
  try {
    instanceData = await ec2.describeInstances(params).promise();
  } catch (e) {
    log("Failed to get instanceData: ", e.stack);
    instanceData = {};
  }
  //log("instanceData: " + JSON.stringify(instanceData));

  // SQS
  params = {
    QueueName: FOQUS_JOB_QUEUE
  };
  try {
    response = await sqs.getQueueUrl(params).promise();
  } catch (e) {
    log("Failed to get queueUrl: ", e.stack);
    response = null;
  }
  //log("sqs.getQueueUrl: " + JSON.stringify(response));
  if (response != null ) {
    params = {
      QueueUrl: response.QueueUrl,
      AttributeNames: [
        'VisibilityTimeout', 'MaximumMessageSize', 'MessageRetentionPeriod', 'ApproximateNumberOfMessages',
        'ApproximateNumberOfMessagesNotVisible', 'ApproximateNumberOfMessagesDelayed', 'DelaySeconds',
        'ReceiveMessageWaitTimeSeconds'
      ]
    };
    try {
      queueData = await sqs.getQueueAttributes(params).promise();
    } catch (e) {
      log("Failed to get queueData: ", e.stack);
      queueData = {};
    }
    //log("queueData: " + JSON.stringify(queueData));
  }

  statusData = JSON.stringify({ autoscale: autoscaleData, ec2: instanceData, sqs: queueData });
  // "jyphn7ci0b.execute-api.us-east-1.amazonaws.com/Prod"
  const endpoint = event.requestContext.domainName + '/' + event.requestContext.stage;
  const apigwManagementApi = new AWS.ApiGatewayManagementApi({
    apiVersion: '2018-11-29',
    endpoint:  endpoint
  });
  log("api gateway endpoint: " + endpoint);
  //const postData = JSON.parse(event.body).data;
  const postCalls = connectionData.Items.map(async ({ Id }) => {
    var connectionId = Id;
    log("connectionId: " + connectionId);
    //log("postData: " + Data);
    try {
      await apigwManagementApi.postToConnection({ ConnectionId: connectionId, Data: statusData }).promise();
    } catch (e) {
      if (e.statusCode === 410) {
        log(`Found stale connection, deleting ${connectionId}`);
        await dynamodb.delete({ TableName: TABLE_NAME,
          Key: {"Id": connectionId, "Type":"WebSocket"} }).promise();
      } else {
        throw e;
      }
    }
  });

  try {
    await Promise.all(postCalls);
  } catch (e) {
    return { statusCode: 500, body: e.stack };
  }

  return { statusCode: 200, body: 'Data sent.' };
};
