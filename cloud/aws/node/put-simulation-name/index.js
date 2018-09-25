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
console.log('Loading function');
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const default_user_name = "anonymous";
const s3_bucket_name = "foqus-simulations";


exports.handler = function(event, context, callback) {
  console.log(`Running index.handler: "${event.httpMethod}"`);
  console.log("event: " + JSON.stringify(event));
  console.log('==================================');
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  if (event.httpMethod == "PUT") {
    var name = event.path.split('/').pop();
    var params = {
      Bucket: s3_bucket_name,
      Body: event.body,
      Key: default_user_name + "/" + name + "/meta.json"
    };
    var client = new AWS.S3();
    //var client = s3.createClient(options);
    client.putObject(params, function(err, data) {
      if (err) console.log(err, err.stack); // an error occurred
      else {
        console.log("Finished: " + data);
        callback(null, {statusCode:'200', body: event.body,
          headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
        });
      }
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  console.log('==================================');
  console.log('Stopping index.handler');
};
