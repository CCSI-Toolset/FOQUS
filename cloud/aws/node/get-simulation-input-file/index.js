/**
 * Lambda Function, returns a simulation input file
 * @module get-simulation-input-file
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
    // PATH: /simulation/test2/input/configuration
    var client = new AWS.S3();
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
    var sim_name = array.pop();
    if (array.pop() != "simulation") {
      done(new Error(`Unsupported path "${event.path}"`));
    }

    var params = {
      Bucket: s3_bucket_name
    };
    if (key == "configuration") {
      params.Prefix = default_user_name + "/" + sim_name + "/";
    }
    else {
      params.Key = default_user_name + "/" + sim_name + "/" + key;
      console.log("FILE RETRIEVE: " + params.Key);
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
    // configuration
    // Search for *.foqus or sinter.json
    console.log("PREFIX: " + params.Prefix);
    client.listObjects(params, function(err, data) {
      if (err) console.log(err, err.stack); // an error occurred
      else {
        console.log("PATH: " + event.path);
        //var name = event.path.split('/').pop();
        // FIND ALL FLOWSHEETS
        var params =  {
          Bucket: s3_bucket_name,
          Key: null
        };
        for (var index = 0; index < data.Contents.length; ++index) {
            var k = data.Contents[index].Key;
            if (k.endsWith(".foqus") || k.endsWith("sinter.json")) {
              var a = k.split('/');
              a.pop();
              console.log("FILE: " + k);
              if (a.pop() != sim_name) continue;
              params.Key = data.Contents[index].Key;
              break;
            }
        }
        if (params.Key != null) {
          console.log("CONFIG RETRIEVE: " + params.Key);
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
      callback(null, {statusCode:'400', body: "configuration not found",
        headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
      });
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  console.log('==================================');
  console.log('Stopping index.handler');
};
