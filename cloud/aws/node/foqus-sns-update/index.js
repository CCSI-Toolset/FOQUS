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
const assert = require('assert');
const log = require("debug")("foqus-sns-update")
const AWS = require('aws-sdk');
const util = require('util');
const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
const tablename = process.env.FOQUS_DYNAMO_TABLE_NAME;
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const log_topic_name = process.env.FOQUS_LOG_TOPIC_NAME;

// TODO: Check Table and skip any items where Finished is already set
var process_session_event_terminate = function(ts, session_id, callback) {
    log(`"process_session_event_terminate(${session_id})"`);
    function dynamoUpdateItems(obj) {
        log(`dynamoUpdateItems:  count=${obj.Count}`);
        log(`dynamoUpdateItems:  ${JSON.stringify(obj)}`);
        if (obj.Count == 0) {
          log("Session contains no jobs");
          return;
        }
        var params = {
          TableName: tablename,
          UpdateExpression: 'SET #f=:f,  #t=:t, #s=:s',
          ExpressionAttributeNames: {"#s": 'state', '#f' : 'finished', '#t':'TTL'},
          ExpressionAttributeValues: {':s': 'terminate', ':f': ts, ':t':Math.floor(Date.now()/1000 + 60*60*12)}
        };
        var item = null;
        var promises = [];
        for(var i=0; i<obj.Count; i++) {
          log(`item:  ${JSON.stringify(obj.Items[i])}`);
          item = {State:"terminate"};
          params.Key = { "Id": obj.Items[i].Id, "Type":"Job" };
          log(`item:  ${JSON.stringify(params)}`);
          var response = dynamodb.update(params);
          promises.push(response.promise());
        }
        Promise.all(promises).then(handleDone).catch(handleError);
    };
    function handleError(error) {
      log(`handleError ${error}`);
      callback(error, "ERROR");
    };
    function handleDone() {
        callback(null, "SUCCESS");
    }
    var params = {
        TableName: tablename,
        KeyConditionExpression: '#T = :job',
        ExpressionAttributeNames: {"#T":"Type"},
        ExpressionAttributeValues: { ":job":"Job", ":sessionid":session_id},
        FilterExpression: 'contains (SessionId, :sessionid)'
    };
    var promise = dynamodb.query(params).promise();
    promise.then(dynamoUpdateItems)
      .then(handleDone)
      .catch(handleError);
};

//
// process_job_event: Adds timestamp to the status field, or if output is
//   specified it adds an output field to item.
//
var process_job_event_output = function(ts, user_name, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    log('process_job_event_output(username= ' + user_name + ')');
    const s3 = new AWS.S3();
    const e = message['event'];
    const status = message['status'];
    const job = message['jobid'];
    const msecs = Date.parse(ts);
    const consumer = message['consumer'];
    const session = message['sessionid']
    const error_message = message['message'];
    const output_obj = message['value'];
    assert.strictEqual(e, "output");
    // NOTE: ValidationException occurring if leave stringify operation
    // to AWS lib json layer.
    const output = JSON.stringify(output_obj);
    log(output);
    var params = {
        TableName:tablename,
        Key:{
            "Id": job,
            "Type":"Job"
        },
        UpdateExpression: "set #w = :o, #t = :t",
        ExpressionAttributeValues:{
            ":o":output,
            ":t":Math.floor(Date.now()/1000 + 60*60*24)
        },
        ExpressionAttributeNames:{
            "#w":"output",
            "#t":"TTL"
        },
        ReturnValues:"UPDATED_NEW"
    };
    publish_to_log_topic(e);
    function handleError(error) {
      log(`handleError ${error.name}`);
      if ( error instanceof Error ) {
        callback(new Error(`"${typeof(error)}"`), "ValidationException")
      }
      callback(new Error(`"${error.stack}"`), "Error")
    };
    function handleDone() {
      log("handleDone");
      callback(null, "Success");
    };
    var response = dynamodb.update(params);
    response.promise()
      .then(handleDone)
      .catch(handleError);
}

var process_job_event_status = function(ts, user_name, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    const log = require("debug")("foqus-sns-update.process_job_event_status")
    const s3 = new AWS.S3();
    const e = message['event'];
    const status = message['status'];
    const job = message['jobid'];
    const msecs = Date.parse(ts);
    const consumer = message['consumer'];
    const session = message['sessionid']
    const error_message = message['message'];
    const milliseconds = (new Date).getTime();

    assert.strictEqual(e, "status");

    log(`status=${status} username=${user_name},  job=${job}, session=${session}`);
    publish_to_log_topic(e);
    function getDynamoJob() {
        // Job is success, put in S3
        log("getDynamoJob: Get Job Description from dynamodb");
        var request = dynamodb.get({ TableName: tablename,
              Key: {"Id": job, "Type": "Job" }
          });
        return request.promise().then(putS3);
    };
    function updateDynamoConsumer() {
        log(`updateDynamoConsumer: Update DynamoDB Consumer=${consumer} with Job=${job}.${status}`);
        var params = {
            TableName:tablename,
            Key:{
                "Id": consumer,
                "Type":"Consumer"
            },
            UpdateExpression: "set #s=:s, #u=:u, #j=:j",
            ExpressionAttributeValues:{
                ":u":user_name,
                ":s":status,
                ":j":job
            },
            ExpressionAttributeNames:{
                "#u":"User",
                "#s":"State",
                "#j":"Job"
            },
            ReturnValues:"UPDATED_NEW"
        };
        log(JSON.stringify(params));
        return dynamodb.update(params).promise();
    }
    function putS3(response) {
        // Job is success, put in S3
        log("putS3: Put Job Description");
        var promise = new Promise(function(resolve, reject){
            if (status=='success' || status=='error' || status=='submit' || status=='setup' || status=='running') {
              response.Item.Output = response.Item.output;
              response.Item.Session = response.Item.SessionId;
              delete response.Item.output;
              delete response.Item.SessionId;
              response.Item.State = status;
              if (status == 'error') {
                log("error: " + error_message);
                response.Item.Message = error_message;
              }
              if (status == 'success' && response.Item.Output == undefined) {
                /* Amazon SNS attempts a retry only after a failed delivery attempt.
                 * Amazon SNS considers the following situations to indicate failed delivery attempts:
                 * HTTP status codes 100 to 101 and 500 to 599 (inclusive).
                 */
                log("Reject Invocation and Retry via HTTP 500: Missing Output");
                throw new Error("Reject Invocation and Retry via HTTP 500: Missing Output")
              }

              var key = `${user_name}/session/${session}/finished/${milliseconds}/${status}/${job}.json`;
              if (status=='submit' || status=='setup' || status=='running') {
                key = `${user_name}/session/${session}/job/${job}/${status}.json`;
              } else if (response.Item.Output != undefined && typeof response.Item.Output == 'string'){
                /* NOTE: DynamoDB's JSON parser can't handle small floats so
                 * decided to store Output column as String in DynamoDB and
                 * parse it to JSON before Stringify and store in S3.
                 */
                response.Item.Output = JSON.parse(response.Item.Output);
              }

              var content = JSON.stringify(response.Item)
              log("put3s: " + content);
              if(content == undefined) {
                throw new Error("s3 object is undefined")
              }
              if(content.length == undefined) {
                throw new Error("s3 object is empty")
              }

              var params = {
                Bucket: s3_bucket_name,
                Key: key,
                Body: content
              };
              log(`putS3(${params.Bucket}):  ${params.Key}`);
              var request = s3.putObject(params);
              resolve(request.promise());
            } else {
              log(`putS3 ignore state ${status}`);
              resolve();
            }
        });
        return promise;
    };
    // function handleError(error) {
    //   log(`handleError  ${error.name}:  Trigger retry`);
    //   //callback(new Error(`"${error.stack}"`), "Error")
    //   callback(null, {statusCode:'500', body: `{"Message":"${error.message}"}`,
    //         headers: {'Content-Type': 'application/json',}});
    // };
    function handleStatusError(error) {
      log(`handleStatusError ${error.name} ${error.stack}`);
      if ( error instanceof Error ) {
        callback(new Error(`"${typeof(error)}"`), "ValidationException")
      }
      callback(new Error(`"${error.stack}"`), "Error")
    };
    function handleDone() {
      log("handleDone");
      callback(null, "Success");
    };

    if (status == 'success' || status == 'error' || status == 'terminate' ) {
        var params = {
            TableName:tablename,
            Key:{
                "Id": job,
                "Type":"Job"
            },
            UpdateExpression: "set #w=:w, #s=:s, ConsumerId=:c, #u=:u, #t=:t",
            ExpressionAttributeValues:{
                ":w":ts,
                ":c":consumer,
                ":u":user_name,
                ":s":status,
                ":t":Math.floor(Date.now()/1000 + 60*60*24)
            },
            ExpressionAttributeNames:{
                "#w":"Finished",
                "#u":"User",
                "#s":"State",
                "#t":"TTL"
            },
            ReturnValues:"UPDATED_NEW"
        };
        log(`finished job: job=${job}, status=${status}`);
        log(JSON.stringify(params));
        var response = dynamodb.update(params);
        response.promise()
          .then(getDynamoJob)
          .then(updateDynamoConsumer)
          .then(handleDone)
          .catch(handleStatusError);
        return;
    }
    if (status == 'expired') {
        var key = `${user_name}/session/${session}/finished/${milliseconds}/expired/${job}.json`;
        var item = {
          Id: job,
          Finished: ts,
          Session: session,
          Status: 'expired',
          Message: 'Consumer failed to find job in database and marked it as expired',
          Consumer: consumer
        };
        var content = JSON.stringify(item);
        var params = {
          Bucket: s3_bucket_name,
          Key: key,
          Body: content
        };
        log(`expired job: job=${job}, status=${status}`);
        var response = s3.putObject(params);
        response.promise()
          .then(putS3)
          .then(handleDone)
          .catch(handleStatusError);
        return;
    }
    if (status == 'submit' | status == 'setup' | status == 'running') {
      var params = {
          TableName:tablename,
          Key:{
              "Id": job,
              "Type":"Job",
          },
          UpdateExpression: "set #w=:s, #t=:t",
          ExpressionAttributeValues:{
              ":s":ts,
              ":t":Math.floor(Date.now()/1000 + 60*60*1)
          },
          ExpressionAttributeNames:{
              "#w":status,
              "#t":'TTL'
          },
          ReturnValues:"UPDATED_NEW"
      };
      if (consumer != undefined ) {
          params.ExpressionAttributeValues[":c"] = consumer;
          params.ExpressionAttributeNames["#c"] = "ConsumerId";
          params.UpdateExpression = "set #w=:s, #t=:t, #c=:c";
      } else {
          log(`status: ${status} consumer: ${consumer}`)
          assert.strictEqual(status, "submit");
      }
      log(`active job: job=${job}, status=${status}`);
      var response = dynamodb.update(params);
      if (status == 'submit') {
          response.promise()
            .then(getDynamoJob)
            .then(handleDone)
            .catch(handleStatusError);
          return;
      }
      response.promise()
        .then(getDynamoJob)
        .then(updateDynamoConsumer)
        .then(handleDone)
        .catch(handleStatusError);
      return;
    }
    assert.fail(`"process_job_event_status, unexpected status ${status}"`);
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
        log(`publish_to_log_topic ${params.Message}`);
        sns.publish(params, function(err, data) {
        });
    });
}

var process_consumer_event = function(ts, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    var e = message['event'];
    //var status = message['status'];
    var consumer = message['consumer'];
    const msecs = Date.parse(ts);
    var instance_id = message['instanceid'];
    var update_expr = "set " + e + " = :s, #t=:t";;
    var expr_attr_vals = {":s":ts, ":t":Math.floor(Date.now()/1000 + 60*60*1)};
    if (instance_id != NaN) {
      update_expr = "set " + e + " =:s, instance=:i, #t=:t";
      expr_attr_vals[":i"] = instance_id;
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
        ExpressionAttributeNames:{
            "#t":"TTL"
        },
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
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
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
    for (var j = 0; j < event.Records.length; j++) {
      var message = JSON.parse(event.Records[j].Sns.Message);
      var attrs = event.Records[j].Sns.MessageAttributes;
      var ts = event.Records[j].Sns.Timestamp;
      //log('Received event:', event.Records[j].Sns.Message);

      if (util.isArray(message) == false) {
          message = [message];
      }

      for (var i = 0; i < message.length; i++) {
          log(`Received event: ${j}.${i}: ${JSON.stringify(message[i])}`);
          //await sleep(2000);
          var resource = message[i]['resource'];
          var e = message[i]['event'];
          if (resource == "job") {
              var user_name = attrs.username.Value;
              if (e == "output") {
                  process_job_event_output(ts, user_name, message[i], callback);
              } else if (e == "status") {
                  process_job_event_status(ts, user_name, message[i], callback);
              } else if (e == "submit") {
                  log(`submit message for job ${message[i].jobid}`)
                  process_job_event_status(ts, user_name, message[i], callback);
              } else {
                assert.fail(`"Job with unknown event ${e}"`);
              }
          } else if (resource == "consumer") {
              process_consumer_event(ts, message[i], callback);
          } else if (attrs.event && attrs.event.Value.startsWith('session.')) {
              const a = attrs.event.Value.split('.');
              const session_id = a[2];
              const state = a[1];
              log(`"session ${session_id}:  event ${state}"`)
              if (state == "terminate")
                process_session_event_terminate(ts, session_id, callback);
              else
                log(`"WARNING: Not Implemented Session ${attrs.event.Value}"`)
          }
          else {
            log("WARNING: NotImplemented skip update resource=" + resource);
          }
      }
    }
    log('Finished');
};
