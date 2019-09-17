/**
 * Lambda Function, lists all files with S3 Prefix s3://bucket/{session_id}/,
 *   get each file which contains a JSON array of job descriptions and Publish
 *   each job to the FOQUS Update Notification topic where the lambda function
 *   foqus-sns-update is listening.
 *
 * @module post-session-start
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
'use uuid'
const log = require("debug")("post-session-start")
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const uuidv4 = require('uuid/v4');
const foqus_update_topic = process.env.FOQUS_UPDATE_TOPIC;

// post-session-start:
//  1.  Grab oldest S3 File in bucket foqus-sessions/{username}/{session_uuid}/*.json
//  2.  Send each job to SNS Job Topic
//  3.  Update DynamoDB TurbineResources table UUID for each job, State=submit, Submit=MS_SINCE_EPOCH
//  4.  Go back to 1
exports.handler = function(event, context, callback) {
  log(`Running index.handler: "${event.httpMethod}"`);
  log("request: " + JSON.stringify(event));
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
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
    log("PATH: " + event.path)
    //var body = JSON.parse(event);
    const session_id = event.path.split('/')[2];
    log("SESSIONID: " + session_id);
    log("SESSION BUCKET_NAME: " + s3_bucket_name);
    var params = {
      Bucket: s3_bucket_name,
      Prefix: user_name + '/' + session_id + '/',
      StartAfter: user_name + '/' + session_id + '/'
    };
    var s3 = new AWS.S3();
    var request_list = s3.listObjectsV2(params, function(err, data) {
        if (err) {
          log(err, err.stack); // an error occurred
          done(new Error(`"${err.stack}"`));
          return;
        }
    });
    request_list.on('success', function(response_list) {
        log("SUCCESS: " + JSON.stringify(response_list.data));
        log("LEN: " + response_list.data.Contents.length);
        log("Create Topic: Name=" + foqus_update_topic);

        var sns = new AWS.SNS();
        var request_topic = sns.createTopic({
            Name: foqus_update_topic,
          }, function(err, data) {
                if (err) {
                  log("ERROR: Failed to SNS CREATE TOPIC");
                  log(err.stack);
                  done(new Error(`"${err.stack}"`));
                  return;
                }
        });
        //
        // List of files {seconds_since_epoch}.json
        // containing Array of job requests
        //
        request_topic.on('success', function(response_topic) {
            var topicArn = response_topic.data.TopicArn;
            log("SUCCESS: " + JSON.stringify(response_topic.data));
            var id_list = [];

            // TAKE S3 LIST OBJECTS
            // Could have multiple S3 objects ( each representing single start )
            var promises = [];
            for (var index = 0; index < response_list.data.Contents.length; index++) {
                var params = {
                  Bucket: s3_bucket_name,
                  Key: response_list.data.Contents[index].Key,
                };
                if (params.Key.endsWith('.json') == false) {
                  log("SKIP: %s", JSON.stringify(params));
                  continue;
                }
                log("PARAMS: %s", JSON.stringify(params));
                // Grab All S3 Files, load them into JSON parsed OBJECTS
                // After all ingested, then send them iterativly to SNS
                // and call done with the number sent.
                // currently this goes file by file.
                let promise = s3.getObject(params).promise();
                promises.push(promise);
              }
              Promise.all(promises).then(function(values) {
                  // return the result to the caller of the Lambda function
                  for (var i=0 ; i < values.length; i++ ) {
                    var data = values[i];
                    var obj = JSON.parse(data.Body.toString('ascii'));
                    log("SESSION(" + session_id + "):  Notify Starting " + obj.length);
                    for (var index=0; index < obj.length; index++) {
                        log("INDEX: " + index);
                        id_list.push(obj[index]['Id']);
                        obj[index].resource = 'job'
                        obj[index].status = 'submit'
                        obj[index].jobid = obj[index].Id
                        obj[index].sessionid = session_id
                        obj[index].consumer = obj[index].consumer;
                        var payload = JSON.stringify(obj[index]);
                        log("Payload: " + payload);
                        var params = {
                            Message: payload,
                            MessageAttributes: {
                              'event': {
                                DataType: 'String',
                                StringValue: 'job.submit'
                              },
                              'username': {
                                DataType: 'String',
                                StringValue: user_name
                              }
                            },
                            TopicArn: topicArn
                        };
                        sns.publish(params, function(err, data) {
                            if (err) {
                              log("ERROR: Failed to SNS Publish Job Start");
                              log(err, err.stack); // an error occurred
                              done(new Error(`"${err.stack}"`));
                              return;
                            }
                        });
                    }
                  }
                  done(null, id_list);
              });
        });
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  log('==================================');
  log('Stopping index.handler');
};
