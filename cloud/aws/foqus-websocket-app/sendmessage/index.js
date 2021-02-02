/**
 * Lambda Function
 *
 * @module sendmessage
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 */
const AWS = require('aws-sdk');
const log = require("debug")("sendmessage")
const dynamodb = new AWS.DynamoDB.DocumentClient({ apiVersion: '2012-08-10', region: process.env.AWS_REGION });
const TABLE_NAME = process.env.FOQUS_WEBSOCKET_TABLE_NAME;
const API_GATEWAY_ENDPOINT = process.env.FOQUS_WEBSOCKET_API_GATEWAY_ENDPOINT

exports.handler = async event => {
  log("request: " + JSON.stringify(event));
  let connectionData;
  var params = {
      TableName: TABLE_NAME,
      KeyConditionExpression: '#T = :websocket',
      ExpressionAttributeNames: {"#T":"Type"},
      ExpressionAttributeValues: { ":websocket":"WebSocket"}
  };
  try {
    //connectionData = await dynamodb.scan({ TableName: TABLE_NAME, ProjectionExpression: 'connectionId' }).promise();
    connectionData = await dynamodb.query(params).promise();
  } catch (e) {
    log("ERROR", e.stack);
    return { statusCode: 500, body: e.stack };
  }
  log("connectionData: " + JSON.stringify(connectionData));
  // "jyphn7ci0b.execute-api.us-east-1.amazonaws.com/Prod"
  const endpoint = event.requestContext.domainName + '/' + event.requestContext.stage;
  const apigwManagementApi = new AWS.ApiGatewayManagementApi({
    apiVersion: '2018-11-29',
    endpoint:  endpoint
  });
  log("api gateway endpoint: " + endpoint);
  const postData = JSON.parse(event.body).data;
  const postCalls = connectionData.Items.map(async ({ Id }) => {
    var connectionId = Id;
    log("connectionId: " + connectionId);
    log("postData: " + postData);
    try {
      await apigwManagementApi.postToConnection({ ConnectionId: connectionId, Data: postData }).promise();
    } catch (e) {
      if (e.statusCode === 410) {
        log(`Found stale connection, deleting ${connectionId}`);
        await dynamodb.delete({ TableName: TABLE_NAME,
          Key: {"Id": event.requestContext.connectionId, "Type":"WebSocket"} }).promise();
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
