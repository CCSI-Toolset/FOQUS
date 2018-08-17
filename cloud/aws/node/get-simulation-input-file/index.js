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

// PATH: /simulation/OUU/input/configuration
exports.handler = function(event, context, callback) {
  console.log(`Running index.handler: "${event.httpMethod}"`);
  console.log("event: " + JSON.stringify(event));
  console.log("query: " + event.queryStringParameters);
  console.log('==================================');
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  if (event.httpMethod == "GET") {
    var params = {
      Bucket: s3_bucket_name,
      Prefix: default_user_name
    };
    var client = new AWS.S3();
    //var client = s3.createClient(options);
    client.listObjects(params, function(err, data) {
      if (err) console.log(err, err.stack); // an error occurred
      else {
        console.log("PATH: " + event.path);
        var name = event.path.split('/').pop();
        // FIND ALL FLOWSHEETS
        for (var index = 0; index < data.Contents.length; ++index) {
            var key = data.Contents[index].Key;
            // key anonymous/{simulation}/input/staged_input
            var short_key = key.split('/').pop();
            console.log("KEY: " + key + ", SHORT KEY: " + short_key + ", NAME: " + name);
            if (name == "configuration") {
                if (key.endsWith('.foqus')) {
                params =  {
                  Bucket: s3_bucket_name,
                  Key: key
                };
                console.log("RETRIEVE: " + key);
                client.getObject(params, function(err, data) {
                   if (err)
                     console.log(err, err.stack); // an error occurred
                   else
                     callback(null, {statusCode:'200', body: data.Body.toString('utf-8'),
                       headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/octet-stream'}
                     });
                });
                return;
              }
            }
            else if (name == short_key) {
              params =  {
                Bucket: s3_bucket_name,
                Key: key
              };
              client.getObject(params, function(err, data) {
                 if (err)
                   console.log(err, err.stack); // an error occurred
                 else
                   callback(null, {statusCode:'200', body: data,
                     headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/octet-stream'}
                   });
              });
              return;
            }
        }
        callback(null, {statusCode:'400', body: "configuration not found",
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
