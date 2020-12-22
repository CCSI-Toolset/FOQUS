/**
 * Lambda Function
 *
 * @module ondisconnect
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 */
const AWS = require('aws-sdk');
const ddb = new AWS.DynamoDB.DocumentClient({ apiVersion: '2012-08-10', region: process.env.AWS_REGION });

exports.handler = async event => {
  log("request: " + JSON.stringify(event));
  var params = {
      TableName: process.env.FOQUS_WEBSOCKET_TABLE_NAME,
      Key: {"Id": event.requestContext.connectionId,
        "Type":"WebSocket"}
  };
  try {
    await ddb.delete(params).promise();
  } catch (err) {
    return { statusCode: 500, body: 'Failed to disconnect: ' + JSON.stringify(err) };
  }

  return { statusCode: 200, body: 'Disconnected.' };
};
