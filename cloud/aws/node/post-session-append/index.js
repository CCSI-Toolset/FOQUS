'use strict';
'use AWS.S3'
'use AWS.DynamoDB'
'use uuid'
// https://github.com/motdotla/node-lambda-template
// NOTE:  CORS For Integrated Lambda Proxy Must be done in Lambda functions
//  because "Integration Response" is disabled, CORS settings will not work!
//  Follow the link:
//     https://stackoverflow.com/questions/40149788/aws-api-gateway-cors-ok-for-options-fail-for-post
//
console.log('Loading function');
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const default_user_name = "anonymous";
const s3_bucket_name = "foqus-sessions";
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
      Key: default_user_name + '/' + session_id + '/' + milliseconds + '.json',
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
            "TurbineResources": items
        }};
        var item = null;
        var i = 0;
        for(var i=0; i<body.length; i++) {
          item = {Id: body[i].Id,
                  Type: "Job",
                  Status: "create",
                  Create: milliseconds+i,
                  SessionId: session_id,
                  User: default_user_name,
                  Application: "foqus"};

          items.push({PutRequest: { Item: item } });
        }
        console.log(JSON.stringify(params));
        var dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
        dynamodb.batchWrite(params, function(err, data) {
          console.log("BATCH WRITE")
          if (err) console.log(err, err.stack); // an error occurred
          else {
            console.log("Unprocessed Items: " + JSON.stringify(data.UnprocessedItems));           // successful response
            callback(null, {statusCode:'200', body: body.length,
              headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'text/plain'}
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
