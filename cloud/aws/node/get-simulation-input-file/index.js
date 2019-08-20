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
const AWS = require('aws-sdk');
const log = require("debug")("get-simulation-input-file");
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const s3_bucket_name = process.env.SIMULATION_BUCKET_NAME;

// PATH: /simulation/OUU/input/configuration
exports.handler = function(event, context, callback) {
  log(`Running index.handler: "${event.httpMethod}"`);
  log("event: " + JSON.stringify(event));
  log("query: " + event.queryStringParameters);
  log('==================================');
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
    log(`KEY: ${key}`);
    if (key == "configuration") {
      if (event.queryStringParameters && event.queryStringParameters.SignedUrl) {
        log("queryStringParameters SignedUrl: unsupported for configuration files");
        callback(null, {statusCode:'406', body:'SignedUrl unsupported for configuration files',
              headers: {'Access-Control-Allow-Origin': '*', 'Content-Type': 'text/plain'}
            });
        return;
      }
      params.Prefix = user_name + "/" + sim_name + "/";
    }
    else if (event.queryStringParameters && event.queryStringParameters.SignedUrl) {
        params.Expires = 120;
        params.Key = user_name + "/" + sim_name + "/" + key;
        log("queryStringParameters SignedUrl, return HTTP 302 with S3 Signed URL for Large Files");
        var s3 = new AWS.S3();
        var url = s3.getSignedUrl('getObject', params);
        //var obj = {"SignedUrl":url};
        callback(null, {statusCode:'302',
              headers: {'Access-Control-Allow-Origin': '*',
                'Location': url }
            });
        return;
    }
    else {
      params.Key = user_name + "/" + sim_name + "/" + key;
      log("FILE RETRIEVE: " + params.Key);
      client.getObject(params, function(err, data) {
        /* FILE RETRIEVE: anonymous/OUU/BFB/BFB_v11_FBS_01_26_2018.acmf
        *  body size is too long
        *  Getting this error when file is > 6MB
        *
        **/
         if (err) {
           log(err, err.stack); // an error occurred
           if (err.code == 'NoSuchKey') {
             callback(null, {statusCode:'404', body: `No such file: ${params.Key}`,
               headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'text/plain'}
             });
           }
         }
         else
           callback(null, {statusCode:'200', body: data.Body.toString('utf-8'),
             headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/octet-stream'}
           });
      });
      return;
    }
    // configuration
    // Search for *.foqus or sinter.json
    log("S3 List: params: " + JSON.stringify(params));
    client.listObjects(params, function(err, data) {
      if (err) log(err, err.stack); // an error occurred
      else {
        //var name = event.path.split('/').pop();
        // FIND ALL FLOWSHEETS
        var params =  {
          Bucket: s3_bucket_name,
          Key: null
        };
        log(`listObjects length: ${data.Contents.length}`);
        for (var index = 0; index < data.Contents.length; ++index) {
            var k = data.Contents[index].Key;
            if (k.endsWith("/session.foqus")) {
              var a = k.split('/');
              a.pop();
              log("Session Foqus file: " + k);
              if (a.pop() != sim_name) continue;
              params.Key = data.Contents[index].Key;
              break;
            }
            if (k.endsWith("_sinter.json")) {
              var a = k.split('/');
              a.pop();
              log("Sinter Configuration File Name: " + k);
              if (a.pop() != sim_name) continue;
              params.Key = data.Contents[index].Key;
              break;
            }
        }
        if (params.Key != null) {
          log("CONFIG RETRIEVE: " + params.Key);
          client.getObject(params, function(err, data) {
             if (err)
               log(err, err.stack); // an error occurred
             else
               callback(null, {statusCode:'200', body: data.Body.toString('utf-8'),
                 headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/octet-stream'}
               });
          });
          return;
        }
      }
      callback(null, {statusCode:'404', body: "input file not found",
        headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'text/plain'}
      });
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  log('==================================');
  log('Stopping index.handler');
};
