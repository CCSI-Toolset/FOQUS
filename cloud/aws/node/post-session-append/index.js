/**
 * Lambda Function, Add an Array of jobs to a Session.
 * Uploads JSON Array of jobs to S3 Session bucket with
 * key "s3://{SESSION_BUCKET_NAME}/user_name/milliseconds_since_epoch.json".
 * Next for each item in array a DynamoDB entry is made in FOQUS_Resources.
 *
 * @module post-session-append
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
'use AWS.DynamoDB'
'use uuid'
const log = require("debug")("post-session-start")
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const uuidv4 = require('uuid/v4');
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const tablename = process.env.FOQUS_DYNAMO_TABLE_NAME;


exports.handler = function(event, context, callback) {
  log(`Running index.handler: "${event.httpMethod}"`);
  log("request: " + JSON.stringify(event));
  log('==================================');
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
  if (event.httpMethod == "POST") {
    log("BODY: " + event.body)
    var body = JSON.parse(event.body);
    var milliseconds = (new Date).getTime();
    var session_id = event.path.substring(event.path.lastIndexOf("/") + 1,
                        event.path.length);
    // Add JOB UUIDS
    for (var i=0; i<body.length; i++) {
      body[i].Id = uuidv4();
    }
    var content = JSON.stringify(body);

    var params = {
      Bucket: s3_bucket_name,
      Key: user_name + '/' + session_id + '/' + milliseconds + '.json',
      Body: content
    };

    var client = new AWS.S3();
    var request = client.putObject(params, function(err, data) {
        if (err) {
          log(err, err.stack);
          done(err);
        }
    });
    request.on('success', function(response) {
        log("S3 SUCCESS: " + JSON.stringify(response.data));
        var items = [];
        var params = {
          RequestItems: {
        }};
        params["RequestItems"][tablename] = items;
        var item = null;
        var i = 0;
        var id_list = [];
        for(var i=0; i<body.length; i++) {
          var d = new Date(milliseconds+i);
          id_list.push(body[i].Id);
          item = {Id: body[i].Id,
                  Type: "Job",
                  Create: d.toISOString(),
                  SessionId: session_id,
                  User: user_name,
                  Initialize: body[i].Initialize,
                  Input: body[i].Input,
                  Reset:body[i].Reset,
                  Simulation: body[i].Simulation,
                  Application: "foqus"};

          items.push({PutRequest: { Item: item } });
        }
        log(JSON.stringify(params));
        var dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
        dynamodb.batchWrite(params, function(err, data) {
          log("BATCH WRITE")
          if (err) {
            log(err, err.stack); // an error occurred
            done(err);
          }
          else {
            log("Unprocessed Items: " + JSON.stringify(data.UnprocessedItems));           // successful response
            callback(null, {statusCode:'200', body: JSON.stringify(id_list),
              headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
            });
          }
        });
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  log('==================================');
  log('Stopping index.handler');
};
