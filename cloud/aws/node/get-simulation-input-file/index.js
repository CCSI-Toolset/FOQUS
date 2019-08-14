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
const s3_bucket_name = process.env.SIMULATION_BUCKET_NAME;

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
    const user_name = event.requestContext.authorizer.principalId;

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
      return;
    }
    var sim_name = array.pop();
    if (array.pop() != "simulation") {
      done(new Error(`Unsupported path "${event.path}"`));
      return;
    }

    var params = {
      Bucket: s3_bucket_name
    };
    if (key == "configuration") {
      params.Prefix = user_name + "/" + sim_name + "/";
    }
    else {
      params.Key = user_name + "/" + sim_name + "/" + key;
      console.log("FILE RETRIEVE: " + params.Key);
      client.getObject(params, function(err, data) {
        /* FILE RETRIEVE: anonymous/OUU/BFB/BFB_v11_FBS_01_26_2018.acmf
        *  body size is too long
        *  Getting this error when file is > 6MB
        *
        **/
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
            if (k.endsWith("/session.foqus")) {
              var a = k.split('/');
              a.pop();
              console.log("FILE: " + k);
              if (a.pop() != sim_name) continue;
              params.Key = data.Contents[index].Key;
              break;
            }
            if (k.endsWith("-sinter.json")) {
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
      callback(null, {statusCode:'404', body: "input file not found",
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
