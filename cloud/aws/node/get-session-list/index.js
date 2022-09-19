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

// Recursive list on $username/session/ prefix
// Appends write timestamped new file to   $username/session/create/$session_id/
// Starts delete all files in $username/session/create/$session_id/ and add the jobs to
// $username/session/$session_id
// aws --profile=foqus s3 ls s3://foquscloudstack-bluefoqussession6a558c90-1fc6967qemecf/boverhof/session/create/
//                           PRE 00700a96-4a3a-4415-821c-27b8a035e181/
//
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/055e58b6-e3f6-4081-820c-51ce262c446e/finished/1657672099030/success/756e0bbc-a43d-4505-95f7-1d387f585802.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/055e58b6-e3f6-4081-820c-51ce262c446e/job/756e0bbc-a43d-4505-95f7-1d387f585802/running.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/055e58b6-e3f6-4081-820c-51ce262c446e/job/756e0bbc-a43d-4505-95f7-1d387f585802/setup.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/055e58b6-e3f6-4081-820c-51ce262c446e/job/756e0bbc-a43d-4505-95f7-1d387f585802/submit.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/62cb73d8-7388-4350-b403-89a8e0d289ab/finished/1657672074522/error/5200006e-4df6-482c-b971-ade75b310ed9.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/62cb73d8-7388-4350-b403-89a8e0d289ab/job/5200006e-4df6-482c-b971-ade75b310ed9/setup.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/62cb73d8-7388-4350-b403-89a8e0d289ab/job/5200006e-4df6-482c-b971-ade75b310ed9/submit.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/c9dcce3c-8e35-4ad0-ba79-f8840f8b3b19/finished/1658256412713/success/02e1ade1-0acd-49bb-904d-ba3f6b0fa036.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/c9dcce3c-8e35-4ad0-ba79-f8840f8b3b19/job/02e1ade1-0acd-49bb-904d-ba3f6b0fa036/running.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/c9dcce3c-8e35-4ad0-ba79-f8840f8b3b19/job/02e1ade1-0acd-49bb-904d-ba3f6b0fa036/setup.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/c9dcce3c-8e35-4ad0-ba79-f8840f8b3b19/job/02e1ade1-0acd-49bb-904d-ba3f6b0fa036/submit.json
// 2022-07-19T19:21:15.922Z get-session-list KEY: boverhof/session/create/00700a96-4a3a-4415-821c-27b8a035e181/1658257902718.json


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
      Prefix: `${user_name}/session/`
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
        var array = null;
        for (var index = 0; index < data.Contents.length; ++index) {
            array = data.Contents[index].Key.split('/');
            value = array[2];
            if (value == 'create') {
              value = array[3];
            }
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
