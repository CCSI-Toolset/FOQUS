/**
 * Name: dynamo-stream-trigger
 * Description:  Listens on DynamoDB stream.  Picks up REMOVE messages for TTL
 * expiration for Consumers it will check the current job for consumer if
 * it is in an active state move the job to error and add a message via
 * SNS Publish.
 *
 * @module foqus-sns-update
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
'use AWS.DynamoDB'
const assert = require('assert');
const log = require("debug")("dynamo-stream-trigger")
const AWS = require('aws-sdk');
const util = require('util');
const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
const tablename = process.env.FOQUS_DYNAMO_TABLE_NAME;
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const log_topic_name = process.env.FOQUS_LOG_TOPIC_NAME;
const update_topic_name = process.env.FOQUS_UPDATE_TOPIC;

var publish_to_update_topic = function(params) {
    var sns = new AWS.SNS();
    var request_topic = sns.createTopic({Name: update_topic_name,}, function(err, data) {
            if (err) {
              log("ERROR: Failed to SNS CREATE TOPIC");
            }
    });
    request_topic.on('success', function(response_topic) {
        var topic_arn = response_topic.data.TopicArn;
        params.TopicArn = topic_arn;
        log(`publish_to_update_topic ${params.Message}`);
        sns.publish(params, function(err, data) {
        });
    });
}



exports.handler = async (event, context) => {
    //log('Received event:', JSON.stringify(event, null, 2));
    //log(`"process_session_event_terminate(${session_id})"`);
    for (const record of event.Records) {
        log(`eventID=${record.eventID} eventName=${record.eventName}`);
        log(`record: ${JSON.stringify(record)}`);
        if (record.eventName == "REMOVE") {
          if (record.dynamodb.Keys.Type != undefined && record.dynamodb.Keys.Type.S == "Consumer") {
            log(`DynamoDB Record Consumer: ${record.dynamodb.Keys.Id.S}`);
            var obj = {};
            obj.event = "status";
            obj.jobid = record.dynamodb.OldImage.Job.S;
            obj.consumer = record.dynamodb.Keys.Id.S;
            obj.status = "terminate";
            obj.resource = "job";
            obj.sessionid = record.dynamodb.OldImage.Session.S;
            obj.message = "consumer expired while job in active state";
            var payload = JSON.stringify(obj);
            var params = {
                Message : payload,
                MessageAttributes: {
                  'event': {
                    DataType: 'String',
                    StringValue: `"job.${obj.status}.${obj.jobid}"`
                  },
                  'username': {
                    DataType: 'String',
                    StringValue: record.dynamodb.OldImage.User.S
                  }
                }
            };
            publish_to_update_topic(params);
          }
        }
    }
    return `Successfully processed ${event.Records.length} records.`;
};
