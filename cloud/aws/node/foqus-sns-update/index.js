/**
 * Lambda Function, listens on a SNS Topic for job notifications.  These
 * notifications are changes of job status, results, etc.
 * @module foqus-sns-update
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
'use uuid'
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
const tablename = 'FOQUS_Resources';
const topic = 'arn:aws:sns:us-east-1:754323349409:FOQUS-Update-Topic';

var process_job_event = function(ts, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    console.log('process_job_event: ' + JSON.stringify(message));
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
        UpdateExpression: "set " + status + " = :s, ConsumerId=:c",
        ExpressionAttributeValues:{
            ":s":ts,
            ":c":consumer
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

    console.log("job(msecs=" + msecs + ") event=" + e);
    console.log(JSON.stringify(params));
    dynamodb.update(params, function(err, data) {
      console.log("Update: " + JSON.stringify(data));
      if (err) {
        // NOTE: data is null, but apparently there is no error when a value is ""
        // ValidationException: ExpressionAttributeValues contains invalid value:
        // One or more parameter values were invalid: An AttributeValue may not contain an empty string for key :o
        console.log(err, err.stack);
        var message = "failed to update dynamodb output field job Id=%s\n%s" %(job,message['value']);
        console.log("publish: " + message);
        var params = {
          Message: message,
          TopicArn: topic
        };
        //console.log("publish: " +  updates[i]);
        sns.publish(params, function(err, data) {
          if (err) console.log(err, err.stack); // an error occurred
          else     console.log(data);           // successful response
        });
        callback(null, "Error");
      } else {
        callback(null, "Success");
      }
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
    console.log("consumer(msecs=" + msecs + ") event=" + e);
    console.log(JSON.stringify(params));
    dynamodb.update(params, function(err, data) {
      console.log("Update: " + data);
      if (err) {
        console.log(err, err.stack);
        callback(null, "Error");
      } else {
        callback(null, "Success");
      }
    });
}

console.log('Loading function');
exports.handler = function(event, context, callback) {
  /*
    "Message": "[{\"status\": \"setup\",
    \"resource\": \"job\",
    \"rc\": 0,
    \"consumer\": \"79cc3b73-97d0-4f5e-b7da-29e011501146\",
    \"event\": \"status\",
    \"job\": \"71d054c2-ca79-4c30-a96b-9078eacd901d\"}]",
  */
    console.log('Received event:', JSON.stringify(event, null, 4));
    console.log('==================================');
    var message = JSON.parse(event.Records[0].Sns.Message);
    var ts = event.Records[0].Sns.Timestamp;
    var params = NaN;
    for (var i = 0; i < message.length; i++) {
      var resource = message[i]['resource'];
      if (resource == "job") {
          process_job_event(ts, message[i], callback);
      } else if (resource == "consumer") {
          process_consumer_event(ts, message[i], callback);
      } else {
        console.log("skip: resource=" + resource);
      }
    }
};
