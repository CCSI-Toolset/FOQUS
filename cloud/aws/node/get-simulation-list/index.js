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
const s3_bucket_name = process.env.SIMULATION_BUCKET_NAME;

// For development/testing purposes
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
  const user_name = event.requestContext.authorizer.principalId;
  if (event.httpMethod == "GET") {
    var params = {
      Bucket: s3_bucket_name,
      Prefix: user_name
    };
    var client = new AWS.S3();
    //var client = s3.createClient(options);
    client.listObjects(params, function(err, data) {
      if (err) console.log(err, err.stack); // an error occurred
      else {
        var foqus_sim_d = new Object();
        var acm_sim_d = new Object();
        var aspenplus_sim_d = new Object();
        var simulation_set = new Set([]);
        var value = "";

        // FIND ALL FLOWSHEETS
        for (var index = 0; index < data.Contents.length; ++index) {
            value = data.Contents[index].Key;
            console.log("XXX: " + value);
            if (value.endsWith('.foqus')) {
              foqus_sim_d[value.split('/')[1]] = new Set([]);
            }
            else if (value.endsWith('acm_sinter.json')) {
              acm_sim_d[value.split('/')[1]] = new Set([]);
            }
            else if (value.endsWith('aspenplus_sinter.json')) {
              aspenplus_sim_d[value.split('/')[1]] = new Set([]);
            }
        }
        if (event.queryStringParameters != null) {
          // CHANGE TO BOOLEAN??
          //var verbose = (event.queryStringParameters.verbose  == 'true');
          var verbose = event.queryStringParameters.verbose;
          console.log("QUERY VERBOSE: " + typeof(verbose));
          console.log("QUERY VERBOSE: " + verbose);
          if (verbose) {
            for (var index = 0; index < data.Contents.length; ++index) {
                value = data.Contents[index].Key;
                var key = value.split('/')[1];
                if (key in foqus_sim_d) {
                  if (value.lastIndexOf('/') != value.length-1) {
                    foqus_sim_d[key].add({Name:value});
                  }
                }
                else if (key in acm_sim_d) {
                  if (value.lastIndexOf('/') != value.length-1) {
                    acm_sim_d[key].add({Name:value});
                  }
                }
                else if (key in aspenplus_sim_d) {
                  if (value.lastIndexOf('/') != value.length-1) {
                    aspenplus_sim_d[key].add({Name:value});
                  }
                }
            }
          }
        }
        for (var key in foqus_sim_d) {
          console.log(foqus_sim_d[key]);
          simulation_set.add({Name:key, Application:"foqus",
            StagedInputs:Array.from(foqus_sim_d[key])});
        }
        for (var key in acm_sim_d) {
          console.log(acm_sim_d[key]);
          simulation_set.add({Name:key, Application:"ACM",
            StagedInputs:Array.from(acm_sim_d[key])});
        }
        for (var key in aspenplus_sim_d) {
          console.log(aspenplus_sim_d[key]);
          simulation_set.add({Name:key, Application:"aspenplus",
            StagedInputs:Array.from(aspenplus_sim_d[key])});
        }
        console.log("SET: " + JSON.stringify(Array.from(simulation_set)));
        var content = JSON.stringify(Array.from(simulation_set));
        console.log("DATA: " + content);           // successful response
        callback(null, {statusCode:'200', body: content,
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
