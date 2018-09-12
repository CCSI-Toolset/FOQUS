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
    var array = event.path.split('/');
    var item = array.pop();
    var key = null;

    if (item == "input") {
      done(new Error(`Unsupported path "${event.path}"`));
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
    }
    var name = array.pop();
    if (array.pop() != "simulation") {
      done(new Error(`Unsupported path "${event.path}"`));
    }

    var params = {
      Bucket: s3_bucket_name,
      Body: event.body
    };

    if (key == "configuration") {
      var obj = JSON.parse(event.body);
      if (obj.filetype == "sinterconfig" && obj.title != undefined) {
        params.Key = default_user_name + "/" + name + "/" + obj.title + "-sinter.json";
      }
      else if (obj.Type == "FOQUS_Session") {
        params.Key = default_user_name + "/" + name + "/session.foqus";
      }
      else {
        done(new Error(`Inspection failed to identify configuration file type`));
        return;
      }
    }
    else {
      params.Key = default_user_name + "/" + name + "/" + key;
    }

    var client = new AWS.S3();
    //var client = s3.createClient(options);
    client.putObject(params, function(err, data) {
      if (err) console.log(err, err.stack); // an error occurred
      else {
        console.log("Finished: " + data);
        callback(null, {statusCode:'200', body: "",
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
