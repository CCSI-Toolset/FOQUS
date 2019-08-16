/**
 * Lambda Function, returns an Array of simulations (UUID).
 * @module get-simulation-list
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
const AWS = require('aws-sdk');
const log = require("debug")("post-simulation-signed-url")
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const s3_bucket_name = process.env.SIMULATION_BUCKET_NAME;


exports.handler = function(event, context, callback) {
  log(`Running index.handler: "${event.httpMethod}"`);
  log("event: " + JSON.stringify(event));
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
  var content_type = event.headers.Accept;
  log(`Header ContentType: ${content_type}`)
  if (event.requestContext.authorizer == null) {
    log("API Gateway Testing");
    var content = JSON.stringify([]);
    callback(null, {statusCode:'200', body: content,
      headers: {'Access-Control-Allow-Origin': '*','Content-Type': content_type}
    });
    return;
  }
  const user_name = event.requestContext.authorizer.principalId;

  if (event.httpMethod == "POST" ) {
    var array = event.path.split('/');
    var item = array.pop();
    var key = null;

    if (item == "input") {
      done(new Error(`Unsupported path "${event.path}"`));
      return;
    }

    while (item != "input") {
      if (key == null) {
        key = item;
      }
      else {
        key = item + "/" + key;
      }
      item = array.pop();
    }
    //var resource = array.pop();
    // simulation/{name}/input/{file_path}
    if (item != "input") {
      done(new Error(`Unsupported path "${event.path}"`));
      return;
    }
    var name = array.pop();
    if (array.pop() != "simulation") {
      done(new Error(`Unsupported path "${event.path}"`));
      return;
    }
    var params = {
      Bucket: s3_bucket_name,
      Expires: 120,
      Key: `${user_name}/${name}/${key}`,
    };
    const method = event.queryStringParameters.method;
    if (method == "putObject") {
      params.ContentType = 'application/json';
    }
    else if (method != "getObject") {
      callback(null, {statusCode:'405', body: `unsupported s3 method: ${method}`,
        headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'text/plain'}
      });
      return;
    }

    const s3 = new AWS.S3();
    log("Params: " + JSON.stringify(params));
    log(`S3 Operation: ${method}`);
    const url = s3.getSignedUrl(method, params);
    log(`SIGNED URL: ${url}`);

    //var obj = {"SignedUrl":url};
    callback(null, {statusCode:'302',
          headers: {'Access-Control-Allow-Origin': '*',
            'ContentType': content_type,
            'Location': url }
        });
    return;
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  log('==================================');
  log('Stopping index.handler');
};
