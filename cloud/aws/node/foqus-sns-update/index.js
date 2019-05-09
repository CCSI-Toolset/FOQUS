/**
 * Name: foqus-sns-update
 * Description:  listens on a FOQUS_UPDATE_TOPIC for update events.  These
 *   notifications are changes of job status, results, etc.
 * @module foqus-sns-update
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use uuid'
const AWS = require('aws-sdk');
const log = require("debug")("foqus-sns-update")
const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
const tablename = process.env.FOQUS_DYNAMO_TABLE_NAME;
//const update_topic_name = process.env.FOQUS_UPDATE_TOPIC;
const job_topic_name = process.env.FOQUS_JOB_TOPIC;

//
// process_job_event: Adds timestamp to the status field, or if output is
//   specified it adds an output field to item.
//
var process_job_event = function(ts, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    log('process_job_event: ' + JSON.stringify(message));
    var e = message['event'];
    var status = message['status'];
    var job = message['jobid'];
    var msecs = Date.parse(ts);
    var consumer = message['consumer'];
    var params = {
        TableName:tablename,
        Key:{
            "Id": job,
            "Type":"Job"
        },
        UpdateExpression: "set #w = :s, ConsumerId=:c",
        ExpressionAttributeValues:{
            ":s":ts,
            ":c":consumer
        },
        ExpressionAttributeNames:{
            "#w":status
        },
        ReturnValues:"UPDATED_NEW"
    };
    if (e == 'output') {
        //var output = JSON.stringify(message['value']['output']);
        var output = message['value'];

        //params.UpdateExpression = "set output=:o";
        //params.ExpressionAttributeValues = {":o":message['value']};
        params = {
            TableName:tablename,
            Key:{
                "Id": job,
                "Type":"Job"
            },
            UpdateExpression: "set #w = :o",
            ExpressionAttributeValues:{
                ":o":output
            },
            ExpressionAttributeNames:{
                "#w":"output"
            },
            ReturnValues:"UPDATED_NEW"
        };
    }

    log("job(msecs=" + msecs + ") event=" + e);
    log(JSON.stringify(params));
    dynamodb.update(params, function(err, data) {
        log("Update: " + JSON.stringify(data));
        if (err) {
          // NOTE: data is null, but apparently there is no error when a value is ""
          // ValidationException: ExpressionAttributeValues contains invalid value:
          // One or more parameter values were invalid: An AttributeValue may not contain an empty string for key :o
          log(err, err.stack);
          var msg = "";
          if (e == 'output')
            msg = "failed to update dynamodb output field job Id=%s\n%s" %(job,message['value']);
          else if (e == 'status')
            msg = "failed to update dynamodb status fields job Id=%s\n%s" %(job,message['status']);
          log("ERROR: " + msg);
          callback(msg, "Error");
        } else {
          publish_to_job_topic(message, callback);
        }
    });
}

var publish_to_job_topic = function(message, callback) {
    var sns = new AWS.SNS();
    var request_topic = sns.createTopic({Name: job_topic_name,}, function(err, data) {
            if (err) {
              log("ERROR: Failed to SNS CREATE TOPIC");
              //log(err);
              callback(new Error(`"${err.stack}"`));
              return;
            }
    });
    request_topic.on('success', function(response_topic) {
        var topic_arn = response_topic.data.TopicArn;
        var params = {
          Message: JSON.stringify(message),
          TopicArn:  topic_arn
        };
        log("SNS Publish: " + topic_arn);
        log(params);
        var sns = new AWS.SNS();
        sns.publish(params, function(err, data) {
            if (err) {
              //log(err, err.stack);
              callback(new Error(`"${err.stack}"`));
            }
            else {
              //log(data);
              callback(null, data);
            }
        });
    });
}

var process_consumer_event = function(ts, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    var e = message['event'];
    //var status = message['status'];
    var consumer = message['consumer'];
    var msecs = Date.parse(ts);
    var instance_id = message['instanceid'];
    var update_expr = "set " + e + " = :s";
    var expr_attr_vals = {":s":ts};
    if (instance_id != NaN) {
      update_expr = "set " + e + " =:s, instance=:i";
      expr_attr_vals = {":s":ts, ":i":instance_id};
    } else {
      instance_id = "None";
    }
    var params = {
        TableName:tablename,
        Key:{
            "Id": consumer,
            "Type":"Consumer"
        },
        UpdateExpression: update_expr,
        ExpressionAttributeValues: expr_attr_vals,
        //ExpressionAttributeNames:{
        //    "#t":"Type"
        //},
        ReturnValues:"UPDATED_NEW"
    };
    log("consumer(msecs=" + msecs + ") event=" + e);
    log(JSON.stringify(params));
    dynamodb.update(params, function(err, data) {
      log("Update: " + data);
      if (err) {
        log(err, err.stack);
        callback(null, "Error");
      } else {
        callback(null, "Success");
      }
    });
}

//
// exports.handler
// Listens to SNS Update Topic, event parameter specifies type of
// resources that are being updated.
//
exports.handler = function(event, context, callback) {
  /*
    "Message": "[{\"status\": \"setup\",
    \"resource\": \"job\",
    \"rc\": 0,
    \"consumer\": \"79cc3b73-97d0-4f5e-b7da-29e011501146\",
    \"event\": \"status\",
    \"job\": \"71d054c2-ca79-4c30-a96b-9078eacd901d\"}]",
  */
    log('Received event:', JSON.stringify(event, null, 4));
    log('==================================');
    var message = JSON.parse(event.Records[0].Sns.Message);
    var ts = event.Records[0].Sns.Timestamp;

    for (var i = 0; i < message.length; i++) {
      var resource = message[i]['resource'];
      if (resource == "job") {
          process_job_event(ts, message[i], callback);
      } else if (resource == "consumer") {
          process_consumer_event(ts, message[i], callback);
      } else {
        log("WARNING: NotImplemented skip update resource=" + resource);
      }
    }
};
