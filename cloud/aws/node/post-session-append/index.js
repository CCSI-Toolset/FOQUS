/**
 * Lambda Function, Add an Array of jobs to a Session
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
console.log('Loading function');
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
//const default_user_name = "anonymous";
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const uuidv4 = require('uuid/v4');

// For development/testing purposes
exports.handler = function(event, context, callback) {
  console.log(`Running index.handler: "${event.httpMethod}"`);
  console.log("request: " + JSON.stringify(event));
  console.log('==================================');
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  const dynamo_put_cb = function (err, res) {
  };
  const user_name = event.requestContext.authorizer.principalId;
  if (event.httpMethod == "POST") {
    console.log("BODY: " + event.body)
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
    //var awsS3Client = new AWS.S3();
    console.log("TESTING...");
    var client = new AWS.S3();
    //var client = s3.createClient(options);
    var request = client.putObject(params, function(err, data) {
        console.log("putObject");
        if (err) console.log(err, err.stack); // an error occurred
        else     console.log("S3 PUTOBJECT")
    });
    request.on('success', function(response) {
        console.log("S3 SUCCESS: " + JSON.stringify(response.data));
        var items = [];
        var params = {
          RequestItems: {
            "FOQUS_Resources": items
        }};
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
        console.log(JSON.stringify(params));
        var dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
        dynamodb.batchWrite(params, function(err, data) {
          console.log("BATCH WRITE")
          if (err) {
            console.log(err, err.stack); // an error occurred
          }
          else {
            console.log("Unprocessed Items: " + JSON.stringify(data.UnprocessedItems));           // successful response
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
  console.log('==================================');
  console.log('Stopping index.handler');
};
