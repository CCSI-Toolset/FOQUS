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
'use AWS.S3'
'use AWS.DynamoDB'
'use uuid'
const log = require("debug")("foqus-sns-update")
const AWS = require('aws-sdk');
const util = require('util');
const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
//const update_topic_name = process.env.FOQUS_UPDATE_TOPIC;
const log_topic_name = process.env.FOQUS_LOG_TOPIC_NAME;
const tablename = process.env.FOQUS_DYNAMO_TABLE_NAME;

//
// process_job_event: Adds timestamp to the status field, or if output is
//   specified it adds an output field to item.
//
var process_job_event = function(ts, user_name, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    log('process_job_event(user= ' + user_name + '): '+ JSON.stringify(message));
    const s3 = new AWS.S3();
    const e = message['event'];
    const status = message['status'];
    const job = message['jobid'];
    const msecs = Date.parse(ts);
    const consumer = message['consumer'];
    const session = message['sessionid']
    var params = {
        TableName:tablename,
        Key:{
            "Id": job,
            "Type":"Job"
        },
        UpdateExpression: "set #w=:s, ConsumerId=:c, #u=:u",
        ExpressionAttributeValues:{
            ":s":ts,
            ":c":consumer,
            ":u":user_name
        },
        ExpressionAttributeNames:{
            "#w":status,
            "#u":"User"
        },
        ReturnValues:"UPDATED_NEW"
    };
    // TODO:  ADD EVENT for Message..
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

    log(JSON.stringify(params));
    publish_to_log_topic(e);

    function getDynamoJob() {
        // Job is success, put in S3
        log("Get Job Description from dynamodb");
        //const milliseconds = (new Date).getTime();
        var request = dynamodb.get({ TableName: tablename,
              Key: {"Id": job, "Type": "Job" }
              //KeyConditionExpression: '#T = :job',
              //ExpressionAttributeNames: {"#T":"Type", "#I":"Id"},
              //ExpressionAttributeValues: { ":job":"Job", ":Id":job}
          });
        return request.promise().then(putS3);
    };

    //var obj = message;
    function putS3(response) {
        // Job is success, put in S3
        const milliseconds = (new Date).getTime();
        var promise = new Promise(function(resolve, reject){
            if (status == 'success' || status == 'error') {
              response.Item.Output = response.Item.output;
              response.Item.Session = response.Item.SessionId;
              delete response.Item.output;
              delete response.Item.SessionId;
              response.Item.State = status;

              var content = JSON.stringify(response.Item)
              log("put3s: " + content);
              if(content == undefined) {
                  throw new Error("s3 object is undefined")
              }
              if(content.length == undefined) {
                  throw new Error("s3 object is empty")
              }
              var key = `${user_name}/session/${session}/finished/${milliseconds}/${status}/${job}.json`;
              var params = {
                Bucket: s3_bucket_name,
                Key: key,
                Body: content
              };
              log(`putS3(${params.Bucket}):  ${params.Key}`);
              var request = s3.putObject(params);
              resolve(request.promise());
            } else {
              log(`putS3 ignore`);
              resolve();
            }
        });
        return promise;
    };
    /*
    dynamodb.update(params, function(err, data) {
        if (err) {
          // NOTE: data is null, but apparently there is no error when a value is ""
          // ValidationException: ExpressionAttributeValues contains invalid value:
          // One or more parameter values were invalid: An AttributeValue may not contain an empty string for key :o
          if (e == 'output')
            log("failed to update dynamodb output field job Id=%s\n%s" %(job,message['value']));
          else if (e == 'status')
            log("failed to update dynamodb status fields job Id=%s\n%s" %(job,message['status']));
          callback(new Error(`"${err.stack}"`));
        } else {
          publish_to_log_topic(message, callback);
        }
    });
    */
    function handleError(error) {
      log(`handleError ${error.name}`);
      callback(new Error(`"${error.stack}"`), "Error")
    };
    function handleDone() {
      log("handleDone");
      callback(null, "Success");
    };
    var response = dynamodb.update(params);
    if (status == 'success' || status == 'error') {
      response.promise()
        .then(getDynamoJob)
        .then(handleDone)
        .catch(handleError);

    } else {
      response.promise()
        .then(handleDone)
        .catch(handleError);
    }
}

var publish_to_log_topic = function(message) {
    var sns = new AWS.SNS();
    var request_topic = sns.createTopic({Name: log_topic_name,}, function(err, data) {
            if (err) {
              log("ERROR: Failed to SNS CREATE TOPIC");
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
        sns.publish(params, function(err, data) {
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

/*
 * exports.handler
 * Listens to SNS Update Topic, event parameter specifies type of
 * resources that are being updated.
 * resource:
 *  job --
 *  consumer --
 *
 */
exports.handler = function(event, context, callback) {
    //log('Received event:', JSON.stringify(event, null, 4));
    var message = JSON.parse(event.Records[0].Sns.Message);
    const attrs = event.Records[0].Sns.MessageAttributes;
    const ts = event.Records[0].Sns.Timestamp;
    log('Received event:', event.Records[0].Sns.Message);
    log('Received event:', event.Records[0].Sns.MessageAttributes.username.Value);
    if (util.isArray(message) == false) {
        message.resource = "job";
        message.event = "submit"
        message = [message];
    }
    for (var i = 0; i < message.length; i++) {
      var resource = message[i]['resource'];
      if (resource == "job") {
          const user_name = attrs.username.Value;
          process_job_event(ts, user_name, message[i], callback);
      } else if (resource == "consumer") {
          process_consumer_event(ts, message[i], callback);
      } else {
        log("WARNING: NotImplemented skip update resource=" + resource);
      }
    }
};
