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
const assert = require('assert');
const AWS = require('aws-sdk');
const util = require('util');
const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
const tablename = process.env.FOQUS_DYNAMO_TABLE_NAME;
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const log_topic_name = process.env.FOQUS_LOG_TOPIC_NAME;
const s3 = new AWS.S3();

/* process_session_start:
 * Check Table and skip any items where Finished is already set
 *    Parmeters:
 *      state -- stop,terminate
 */
var process_session_stop = function(state, ts, session_id, callback) {
    console.log(`"process_session_stop(${state}, ${session_id})"`);
    function dynamoUpdateItems(obj) {
        console.log(`dynamoUpdateItems:  count=${obj.Count}`);
        console.log(`dynamoUpdateItems:  ${JSON.stringify(obj)}`);
        if (obj.Count == 0) {
          console.log("Session contains no jobs in status submit");
          return;
        }
        var params = {
            TableName: tablename,
            UpdateExpression: 'SET #t=:t, #s=:s',
            ExpressionAttributeNames: {"#s": 'State', '#t':'TTL'},
            ExpressionAttributeValues: {':s': state, ':sid':session_id, ':t':Math.floor(Date.now()/1000 + 60*60*12)},
            ConditionExpression: 'contains (SessionId, :sid) and (#s in (submit))'
        };
        var promises = [];
        for(var i=0; i<obj.Count; i++) {
          console.log(`item:  ${JSON.stringify(obj.Items[i])}`);
          params.Key = { "Id": obj.Items[i].Id, "Type":"Job" };
          console.log(`item:  ${JSON.stringify(params)}`);
          var response = dynamodb.update(params);
          promises.push(response.promise());
        }
        Promise.all(promises).then(handleDone).catch(handleError);
    };
    function handleError(error) {
      console.log(`handleError ${error}`);
      callback(error, "ERROR");
    };
    function handleDone() {
        callback(null, "SUCCESS");
    }
    var params = {
        TableName: tablename,
        KeyConditionExpression: '#T = :job',
        ExpressionAttributeNames: {"#T":"Type", "#S":"State"},
        ExpressionAttributeValues: { ":job":"Job", ":sessionid":session_id},
        FilterExpression: 'contains (SessionId, :sessionid) and (#S in (submit))'
    };
    var promise = dynamodb.query(params).promise();
    promise.then(dynamoUpdateItems)
      .then(handleDone)
      .catch(handleError);
};

/*
 * process_session_start:  Moves DynamoDB Jobs in session_id
 *     from stop to submit
 */
var process_session_start = function(ts, session_id, callback) {
    console.log(`process_session_start(${session_id})`);
    function dynamoUpdateItems(obj) {
        console.log(`dynamoUpdateItems:  count=${obj.Count}`);
        console.log(`dynamoUpdateItems:  ${JSON.stringify(obj)}`);
        if (obj.Count == 0) {
          console.log("Session contains no jobs");
          return;
        }
        // ONLY job.stop can be moved to job.submit here
        // process-session-start generates SNS msg for each job.create and one session.start
        // worker ignores SQS Message with job.stop
        var params = {
          TableName: tablename,
          UpdateExpression: 'SET #t=:t, #s=:s',
          ExpressionAttributeNames: {"#s": 'State', '#t':'TTL'},
          ExpressionAttributeValues: {':s': 'submit', ':sid':session_id, ':t':Math.floor(Date.now()/1000 + 60*60*12)},
          FilterExpression: 'contains (SessionId, :sid) and (#s in (stop))'
        };
        var item = null;
        var promises = [];
        for(var i=0; i<obj.Count; i++) {
          console.log(`item:  ${JSON.stringify(obj.Items[i])}`);
          params.Key = { "Id": obj.Items[i].Id, "Type":"Job" };
          console.log(`params:  ${JSON.stringify(params)}`);
          var response = dynamodb.update(params);
          promises.push(response.promise());
        }
        Promise.all(promises).then(handleDone).catch(handleError);
    };
    function handleError(error) {
      console.log(`handleError ${error}`);
      callback(error, "ERROR");
    };
    function handleDone() {
        callback(null, "SUCCESS");
    }
    var params = {
          TableName: tablename,
          KeyConditionExpression: '#T = :job',
          ExpressionAttributeNames: {"#T":"Type", "#S":"State"},
          ExpressionAttributeValues: { ":job":"Job", ":sessionid":session_id},
          FilterExpression: 'contains (SessionId, :sessionid) and (#S in (stop))'
    };
    var promise = dynamodb.query(params).promise();
    promise.then(dynamoUpdateItems)
      .then(handleDone)
      .catch(handleError);
};

var process_session_terminate = function(ts, session_id, user_name, callback) {
    console.log(`"process_session_terminate(${session_id})"`);
    // dynamoUpdateItemsTerminate:  Move all jobs in session to status terminate
    function dynamoUpdateItemsTerminate(obj) {
        console.log(`dynamoUpdateItemsTerminate:  count=${obj.Count}`);
        console.log(`dynamoUpdateItemsTerminate:  ${JSON.stringify(obj)}`);
        if (obj.Count == 0) {
          console.log("Session contains no jobs");
          return;
        }
        var params = {
          TableName: tablename,
          UpdateExpression: 'SET #f=:f,  #t=:t, #s=:s',
          ExpressionAttributeNames: {"#s": 'State', '#f' : 'Finished', '#t':'TTL'},
          ExpressionAttributeValues: {':s': 'terminate', ':f': ts, ':t':Math.floor(Date.now()/1000 + 60*60*12)},
          FilterExpression: 'contains (SessionId, :sid) and (#s in (submit, stop, setup, running))'
        };
        var promises = [];
        for(var i=0; i<obj.Count; i++) {
          console.log(`item:  ${JSON.stringify(obj.Items[i])}`);
          params.Key = { "Id": obj.Items[i].Id, "Type":"Job" };
          console.log(`params:  ${JSON.stringify(params)}`);
          var response = dynamodb.update(params);
          promises.push(response.promise());
        }
        return Promise.all(promises);
    };
    // listDeleteS3Objects:  Delete all S3 keys prefixed {session_id}/create
    function listDeleteS3Objects(obj) {
        if (obj) {
          console.log(`listDeleteS3Objects: Number Updated jobs: ${obj.Count}`)
        }
        else {
          console.log(`listDeleteS3Objects: DynamoDB Query returned nothing`);
        }
        var promises = [];
        var promise = null;
        var params_list = {Bucket: s3_bucket_name, Prefix:`${user_name}/session/create/${session_id}/`};;
        function deleteObjects(listedObjects) {
          console.log(`listedObjects: ${JSON.stringify(listedObjects)}`);
          if (!listedObjects.KeyCount) {
              return;
          }
          var params = {Bucket: s3_bucket_name, Delete:{Objects:[]}};
          listedObjects.Contents.forEach(({ Key }) => {
              params.Delete.Objects.push({ Key });
          });
          var promise = s3.deleteObjects(params, function(err, data) {
              if (err) {
                  console.log(`listDeleteS3Objects(${params.Delete.Objects}), ERROR: ${err}`);
                  console.log(`listDeleteS3Objects ERROR Stack: ${err.stack}`);
                  throw new Error(`Failed to s3.deleteObjects Prefix=${params_list.Prefix}`);
              } else {
                  console.log(`listDeleteS3Objects: DELETED ${params.Objects}`);
              }
          });
        }
        promise = s3.listObjectsV2(params_list).promise();
        promise.then(deleteObjects);
        return promise;
    };
    function handleError(error) {
      console.log(`handleError ${error}`);
      callback(error, "ERROR");
    };
    function handleDone() {
        callback(null, "SUCCESS");
    }
    var promise = null;
    var params = {
        TableName: tablename,
        KeyConditionExpression: '#T = :job',
        ExpressionAttributeNames: {"#s": 'State',"#T":"Type"},
        ExpressionAttributeValues: { ":job":"Job", ":sid":session_id, ":create":"create"},
        FilterExpression: 'contains (SessionId, :sid) and (#s in (:create, submit, stop, setup, running))'
    };
    promise = dynamodb.query(params).promise();
    promise.then(dynamoUpdateItemsTerminate)
      .then(listDeleteS3Objects)
      .then(handleDone)
      .catch(handleError);
};

//
// process_job_event: Adds timestamp to the status field, or if output is
//   specified it adds an output field to item.
//
var process_job_event_output = function(ts, user_name, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    console.log('process_job_event_output(username= ' + user_name + ')');
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
    console.log(output);
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
      console.log(`handleError ${error.name}`);
      if ( error instanceof Error ) {
        callback(new Error(`"${typeof(error)}"`), "ValidationException")
      }
      callback(new Error(`"${error.stack}"`), "Error")
    };
    function handleDone() {
      console.log("handleDone");
      callback(null, "Success");
    };
    var response = dynamodb.update(params);
    response.promise()
      .then(handleDone)
      .catch(handleError);
}

/*
 * Function: process_job_event_status
 * process_job_event_output happens before "success", output is saved to
 * the DynamoDB table under "output", then job event status success is fired
 * and the DynamoDB item is retrieved and those values are used to store
 * back in S3.
 */
var process_job_event_status = function(ts, user_name, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    const e = message['event'];
    const status = message['status'];
    const job = message['jobid'];
    const msecs = Date.parse(ts);
    const consumer = message['consumer'];
    const session = message['sessionid']
    const error_message = message['message'];
    const milliseconds = (new Date).getTime();

    assert.strictEqual(e, "status");

    console.log(`status=${status} username=${user_name},  job=${job}, session=${session}`);
    publish_to_log_topic(e);
    function getDynamoJob() {
        // Job is success, put in S3
        console.log("getDynamoJob: Get Job Description from dynamodb");
        var request = dynamodb.get({ TableName: tablename,
              Key: {"Id": job, "Type": "Job" }
          });
        return request.promise().then(putS3);
    };
    function updateDynamoConsumer() {
        console.log(`updateDynamoConsumer: Update DynamoDB Consumer=${consumer} with Job=${job}.${status}`);
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
                "#j":"Job",
            },
            ReturnValues:"UPDATED_NEW"
        };
        if (session != undefined) {
            params.ExpressionAttributeValues[":n"] = session;
            params.ExpressionAttributeNames["#n"] = "Session";
            params.UpdateExpression = "set #s=:s, #u=:u, #j=:j, #n=:n";
        }
        console.log(JSON.stringify(params));
        return dynamodb.update(params).promise();
    }
    function putS3(response) {
        // Job is success, put in S3
        console.log("putS3: Put Job Description");
        var promise = new Promise(function(resolve, reject){
            if (status=='success' || status=='error' || status=='submit' || status=='setup' || status=='running') {
              if (response.Item.Output == undefined) {
                // NOTE: map output to Output ( remove?? )
                response.Item.Output = response.Item.output;
              }
              response.Item.Session = response.Item.SessionId;
              delete response.Item.output;
              delete response.Item.SessionId;
              response.Item.State = status;
              if (status == 'error') {
                console.log("error: " + error_message);
                response.Item.Message = error_message;
              }
              if (status == 'success' && response.Item.Output == undefined) {
                /* Amazon SNS attempts a retry only after a failed delivery attempt.
                 * Amazon SNS considers the following situations to indicate failed delivery attempts:
                 * HTTP status codes 100 to 101 and 500 to 599 (inclusive).
                 */
                console.log(`Session ${response.Item.Session}/Job ${response.Item.Id}:  No Output`);
                //throw new Error("Reject Invocation and Retry via HTTP 500: Missing Output")
                response.Item.Message = "Processing Error: No Simulation Output";
              }

              var key = `${user_name}/session/${session}/finished/${milliseconds}/${status}/${job}.json`;
              if (status=='submit' || status=='setup' || status=='running') {
                key = `${user_name}/session/${session}/job/${job}/${status}.json`;
              } else if (response.Item.Output != undefined && typeof response.Item.Output == 'string'){
                /* NOTE: DynamoDB's JSON parser can't handle small floats so
                 * decided to store Output column as String in DynamoDB and
                 * parse it to JSON before Stringify and store in S3.
                 */
                 try {
                    response.Item.Output = JSON.parse(response.Item.Output);
                 }
                 catch(error) {
                    console.log(error);
                    response.Item.Message = "Processing Error: Failed to parse Simulation Output";
                 }
              }

              var content = JSON.stringify(response.Item)
              console.log("put3s: " + content);
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
              console.log(`putS3(${params.Bucket}):  ${params.Key}`);
              var request = s3.putObject(params);
              resolve(request.promise());
            } else {
              console.log(`putS3 ignore state ${status}`);
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
      console.log(`handleStatusError ${error.name} ${error.stack}`);
      if ( error instanceof Error ) {
        callback(new Error(`"${typeof(error)}"`), "ValidationException")
      }
      callback(new Error(`"${error.stack}"`), "Error")
    };
    function handleDone() {
      console.log("handleDone");
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
            ConditionExpression: 'not ( #s in (submit,:e,terminate))',
            ExpressionAttributeValues:{
                ":w":ts,
                ":c":consumer,
                ":u":user_name,
                ":e":"error",
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
        console.log(`finished job: job=${job}, status=${status}`);
        console.log(JSON.stringify(params));
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
        console.log(`expired job: job=${job}, status=${status}`);
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
          console.log(`status: ${status} consumer: ${consumer}`)
          assert.strictEqual(status, "submit");
      }
      console.log(`active job: job=${job}, status=${status}`);
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
              console.log("ERROR: Failed to SNS CREATE TOPIC");
            }
    });
    request_topic.on('success', function(response_topic) {
        var topic_arn = response_topic.data.TopicArn;
        var params = {
          Message: JSON.stringify(message),
          TopicArn:  topic_arn
        };
        console.log(`publish_to_log_topic ${params.Message}`);
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
    if (isNaN(instance_id)) {
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
    console.log(`EVENT: ${JSON.stringify(event)}`);
    if (!event.Records) {
      console.log('Finished: No SNS Records');
      return;
    }
    for (var j = 0; j < event.Records.length; j++) {
      var attrs = event.Records[j].Sns.MessageAttributes;
      var user_name = attrs.username.Value;
      var ts = event.Records[j].Sns.Timestamp;
      if (attrs.event && attrs.event.Value.startsWith('session.')) {
          const a = attrs.event.Value.split('.');
          const session_id = a[2];
          const state = a[1];
          console.log(`"session ${session_id}:  event ${state}"`)
          if (state == "kill")
              process_session_terminate(ts, session_id, user_name, callback);
          else if (state == "stop")
              process_session_stop(ts, session_id, callback);
          else if (state == "start")
              process_session_start(ts, session_id, callback);
          else
              console.log(`"WARNING: Not Implemented Session ${attrs.event.Value}"`)
          continue;
      }

      var message = JSON.parse(event.Records[j].Sns.Message);
      if (util.isArray(message) == false) {
          message = [message];
      }
      console.log(`SNS MessageAttributes: ${j}: ${JSON.stringify(attrs)}`);
      for (var i = 0; i < message.length; i++) {
          console.log(`Received event: ${j}.${i}: ${JSON.stringify(message[i])}`);
          //await sleep(2000);
          var resource = message[i]['resource'];
          var e = message[i]['event'];
          if (resource == "job") {
              if (!attrs.username) {
                  assert.fail(`"MessageAttributes.username not defined: ${attrs.username}"`);
              }
              if (!user_name) {
                  assert.fail("MessageAttributes.username.Value undefined");
              }
              if (e == "output") {
                  process_job_event_output(ts, user_name, message[i], callback);
              } else if (e == "status") {
                  process_job_event_status(ts, user_name, message[i], callback);
              } else if (e == "submit") {
                  console.log(`submit message for job ${message[i].jobid}`)
                  process_job_event_status(ts, user_name, message[i], callback);
              } else {
                assert.fail(`"Job with unknown event ${e}"`);
              }
          } else if (resource == "consumer") {
              process_consumer_event(ts, message[i], callback);
          }
          else {
            console.log("WARNING: NotImplemented skip update resource=" + resource);
          }
      }
    }
    console.log('Finished');
};
