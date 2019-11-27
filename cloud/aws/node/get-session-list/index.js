/**
 * Lambda Function, returns an Array of sessions (UUID).
 * @module get-session-list
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
//const default_user_name = "anonymous";
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const log = require("debug")("get-session-list")

// For development/testing purposes
exports.handler = function(event, context, callback) {
  log(`Running index.handler: "${event.httpMethod}"`);
  log("request: " + JSON.stringify(event));
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  if (event.requestContext == null) {
    context.fail("No requestContext for user mapping")
    return;
  }
  if (event.requestContext.authorizer == null) {
    log("API Gateway Testing");
    var content = JSON.stringify([]);
    callback(null, {statusCode:'200', body: content,
      headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
    });
    return;
  }
  const user_name = event.requestContext.authorizer.principalId;
  if (event.httpMethod == "GET") {
    var params = {
      Bucket: s3_bucket_name,
      Prefix: `${user_name}/session/create/`
    };
    //var awsS3Client = new AWS.S3();
    log(`SESSION GET: ${JSON.stringify(params)}`);
    var client = new AWS.S3();
    //var client = s3.createClient(options);
    client.listObjectsV2(params, function(err, data) {
      if (err) log(err, err.stack); // an error occurred
      else {
        var session_set = new Set([]);
        var value = "";
        for (var index = 0; index < data.Contents.length; ++index) {
            value = data.Contents[index].Key;
            value = value.split('/')[3];
            session_set.add(value);
        }
        var content = JSON.stringify(Array.from(session_set));
        log("S3 List Objects: " + content);
        callback(null, {statusCode:'200', body: content,
          headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
      });
      }
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
};
