'use strict';
'use AWS.S3'
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

// POST SESSION START:
//  1.  Grab oldest S3 File in bucket foqus-sessions/{username}/{session_uuid}/*.json
//  2.  Send each job to SNS Job Topic
//  3.  Update DynamoDB TurbineResources table UUID for each job, State=submit, Submit=MS_SINCE_EPOCH
//  4.  Go back to 1
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
  if (event.httpMethod == "POST") {
    console.log("PATH: " + event.path)
    //var body = JSON.parse(event);
    var session_id = event.path.split('/')[2];
    console.log("SESSIONID: " + session_id);

    var params = {
      Bucket: s3_bucket_name,
      Prefix: default_user_name + '/' + session_id
    };
    var client = new AWS.S3();
    var request = client.listObjects(params, function(err, data) {
        if (err) console.log(err, err.stack); // an error occurred
        else     console.log("DATA: " + data);
    });
    request.on('success', function(response) {
        console.log("SUCCESS: " + JSON.stringify(response.data));
        console.log("LEN: " + response.data.Contents.length)

        var sns = new AWS.SNS();
        var request = sns.createTopic({
            Name: 'FOQUS-Job-Topic'
          }, function(err, data) {
                if (err) console.log(err.stack);
                else     console.log("TOPIC: " + JSON.stringify(data));
        });
        request.on('success', function(response_topic) {

            var topicArn = response_topic.data.TopicArn;
            console.log("SUCCESS: " + JSON.stringify(response_topic.data));
            // TAKE S3 LIST OBJECTS
            for (var index = 0; index < response.data.Contents.length; index++) {
                var params = {
                  Bucket: s3_bucket_name,
                  Key: response.data.Contents[index].Key,
                };
                var request = client.getObject(params, function(err, data) {
                  if (err) console.log(err, err.stack); // an error occurred
                  else {
                    var obj = JSON.parse(data.Body.toString('ascii'));
                    console.log("SESSION: " + JSON.stringify(obj));
                    for (var index=0; index < obj.length; index++) {
                      console.log("INDEX: " + index);
                      var payload = JSON.stringify(obj[index]);
                      console.log("Payload: " + payload);
                      var params = {
                        Message: payload,
                        TopicArn: topicArn
                      };
                      sns.publish(params, function(err, data) {
                        if (err) console.log(err, err.stack); // an error occurred
                        else     console.log("PUBLISH: " + JSON.stringify(data));           // successful response
                      });
                    }
                  }
                });
            }
        });

        callback(null, {statusCode:'200', body: "",
          headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'text/plain'}
        });
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  console.log('==================================');
  console.log('Stopping index.handler');
};
