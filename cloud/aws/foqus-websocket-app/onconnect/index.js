/**
 * Lambda Function
 *
 * @module onconnect
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 */
const AWS = require('aws-sdk');
const log = require("debug")("onconnect")
const ddb = new AWS.DynamoDB.DocumentClient({ apiVersion: '2012-08-10', region: process.env.AWS_REGION });

exports.handler = async event => {
  log("request: " + JSON.stringify(event));
  const putParams = {
    TableName: process.env.FOQUS_WEBSOCKET_TABLE_NAME,
    Item: {
      Type: "WebSocket",
      Id: event.requestContext.connectionId,
      Username: event.requestContext.authorizer.principalId,
      TTL: Math.floor(Date.now()/1000 + 60*30)
    }
  };

  try {
    await ddb.put(putParams).promise();
  } catch (err) {
    return { statusCode: 500, body: 'Failed to connect: ' + JSON.stringify(err) };
  }

  return { statusCode: 200, body: 'Connected.' };
};
