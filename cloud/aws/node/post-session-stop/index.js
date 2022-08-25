/**
 * Lambda Function, Moves all submitted jobs to stop.  Stopped jobs remain
 * on the job queue but will be ignored until moved back to submit or deleted if
 * moved to terminate.
 *
 * @module post-session-stop
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.SNS'
'use uuid'
const log = require("debug")("post-session-stop")
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
//const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
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
    const state = event.path.split('/')[3];
    var sns = new AWS.SNS();
    log("foqus_update_topic: " + foqus_update_topic);
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
    request_topic.on('success', function(response_topic) {
        var topicArn = response_topic.data.TopicArn;
        log("SUCCESS: " + JSON.stringify(response_topic.data));
        var obj = {};
        obj.id = session_id;
        obj.status = "stop";
        obj.resource = "session";
        obj.message = "user initiated stop session";
        var payload = JSON.stringify(obj);
        var params = {
            Message : payload,
            MessageAttributes: {
              'event': {
                DataType: 'String',
                StringValue: `session.${state}.${session_id}`
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
            done(null, session_id);
        });
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  log('==================================');
  log('Stopping index.handler');
};
