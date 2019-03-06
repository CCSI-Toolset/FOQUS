/**
 * Lambda Function, moves all jobs in session from state 'create|pause' to
 * 'submit'.
 * @module post-session-start
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
'use uuid'
console.log('Loading function');
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
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
          'Access-Control-Allow-Origin': '*'
      },
  });
  const user_name = event.requestContext.authorizer.principalId;
  if (event.httpMethod == "POST") {
    console.log("PATH: " + event.path)
    //var body = JSON.parse(event);
    var session_id = event.path.split('/')[2];
    console.log("SESSIONID: " + session_id);

    var params = {
      Bucket: s3_bucket_name,
      Prefix: user_name + '/' + session_id
    };
    var client = new AWS.S3();
    var request = client.listObjects(params, function(err, data) {
        if (err) {
          console.log(err, err.stack); // an error occurred
          done(new Error(`"${err.stack}"`));
          return;
        }
        else     console.log("DATA: " + data);
    });
    request.on('success', function(response) {
        console.log("SUCCESS: " + JSON.stringify(response.data));
        console.log("LEN: " + response.data.Contents.length)

        var sns = new AWS.SNS();
        var request_topic = sns.createTopic({
            Name: 'FOQUS-Job-Topic'
          }, function(err, data) {
                if (err) {
                  console.log(err.stack);
                  done(new Error(`"${err.stack}"`));
                  return;
                }
                else     console.log("TOPIC: " + JSON.stringify(data));
        });
        request_topic.on('success', function(response_topic) {

            var topicArn = response_topic.data.TopicArn;
            console.log("SUCCESS: " + JSON.stringify(response_topic.data));
            var id_list = [];

            // TAKE S3 LIST OBJECTS
            // Could have multiple S3 objects ( each representing single start )
            for (var index = 0; index < response.data.Contents.length; index++) {
                var params = {
                  Bucket: s3_bucket_name,
                  Key: response.data.Contents[index].Key,
                };
                var request = client.getObject(params, function(err, data) {
                  if (err) {
                    console.log(err, err.stack); // an error occurred
                    done(new Error(`"${err.stack}"`));
                    return;
                  }
                  else {
                    var obj = JSON.parse(data.Body.toString('ascii'));
                    console.log("SESSION: " + JSON.stringify(obj));
                    for (var index=0; index < obj.length; index++) {
                      console.log("INDEX: " + index);
                      id_list.push(obj[index]['Id']);
                      var payload = JSON.stringify(obj[index]);
                      console.log("Payload: " + payload);
                      var params = {
                        Message: payload,
                        TopicArn: topicArn
                      };
                      sns.publish(params, function(err, data) {
                        if (err) {
                          console.log("ERROR")
                          console.log(err, err.stack); // an error occurred
                          //done(new Error(`"${err.stack}"`));
                          //done(new Error(`SNS Publish ERROR:   "${err.stack}"`));
                          //return;
                        }
                        else  {
                          console.log("PUBLISH: " + JSON.stringify(data));           // successful response
                        }
                      });
                    }
                    done(null, id_list);
                  }
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
