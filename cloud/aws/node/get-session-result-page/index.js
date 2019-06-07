/**
 * Lambda Function, returns an Array of simulations (UUID).
 * @module get-session-result-page
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
const log = require("debug")("post-session-start")
log('Loading function');
const AWS = require('aws-sdk');
const path = require('path');
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;

// PATH: /session/{GUID}/result/{GUID}/{page_num}
exports.handler = function(event, context, callback) {
  log(`Running index.handler: "${event.httpMethod}"`);
  log("event: " + JSON.stringify(event));
  log("query: " + event.queryStringParameters);
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  if (event.httpMethod == "GET") {
    log("PATH: " + event.path);
    const user_name = event.requestContext.authorizer.principalId;
      var path = event.path.split('/');
      var page = path.pop();
      var gen_id = path.pop();
      if (path.pop() != "result") {
        done(new Error(`Unsupported method "${event.httpMethod}"`));
        return;
      }
      var session_id = path.pop();

      var params = {
        Bucket: s3_bucket_name,
        Key: user_name + '/' + session_id + "/" + gen_id + "/" + page + '.json',
      };
      log("PARAMS: " + JSON.stringify(params));
      var client = new AWS.S3();
      client.getObject(params, function(err, data) {
         if (err)
           log(err, err.stack); // an error occurred
         else
           callback(null, {statusCode:'200', body: data.Body.toString('utf-8'),
             headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/octet-stream'}
           });
      });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  log('Stopping index.handler');
};
