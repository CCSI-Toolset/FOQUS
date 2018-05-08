'use strict';
'use AWS.S3'
'use uuid'
// https://github.com/motdotla/node-lambda-template
// NOTE:  CORS For Integrated Lambda Proxy Must be done in Lambda functions
//  because "Integration Response" is disabled, CORS settings will not work!
//  Follow the link:
//     https://stackoverflow.com/questions/40149788/aws-api-gateway-cors-ok-for-options-fail-for-post
//
console.log('Loading function');
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const default_user_name = "anonymous";
const s3_bucket_name = "foqus-sessions";
const uuidv4 = require('uuid/v4');

// For development/testing purposes
exports.handler = function(event, context, callback) {
  console.log(`Running index.handler: "${event.httpMethod}"`);
  console.log("request: " + JSON.stringify(event));
  console.log('==================================');
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  if (event.httpMethod == "POST") {
    console.log("BODY: " + event.body)
    var body = JSON.parse(event.body);
    var session_id = uuidv4();
    //var content = JSON.stringify(obj);
    callback(null, {statusCode:'200', body: session_id,
      headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/text'}
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  console.log('==================================');
  console.log('Stopping index.handler');
};
