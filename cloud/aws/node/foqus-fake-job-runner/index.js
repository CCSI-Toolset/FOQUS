/**
 * Pops job off SQS Job queue and sends canned notifications to SNS Publish Topic
 * which will cause foqus-sns-update to create job updates.
 *
 * @module foqus-fake-job-runner
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
'use uuid'
const AWS = require('aws-sdk');
const sqs = new AWS.SQS();
const sns = new AWS.SNS();
const queue_name = process.env.FOQUS_JOB_QUEUE;
const update_topic_name = process.env.FOQUS_UPDATE_TOPIC;
const log = require("debug")("foqus-fake-job-runner")


exports.handler = function(event, context, callback) {
  /*
    "Message": "[{"status\": \"setup\",
    \"resource\": \"job\",
    \"rc\": 0,
    \"consumer\": \"79cc3b73-97d0-4f5e-b7da-29e011501146\",
    \"event\": \"status\",
    \"job\": \"71d054c2-ca79-4c30-a96b-9078eacd901d\"}]",
  */
    //console.log('Received event:', JSON.stringify(event, null, 4));

    var request = sns.createTopic({Name: update_topic_name,});
    var promise = request.promise();
    promise.then(handleGetQueueURL)
      .then(handleGetQueueData)
      .then(handleProcessQueueData)
      .catch(handleError);

    var update_topic_arn = "";
    function handleGetQueueURL(data) {
        log("handleGetQueueURL: " + JSON.stringify(data));
        update_topic_arn = data.TopicArn;
        var response =  sqs.getQueueUrl({QueueName: queue_name});
        return response.promise();
    };
    var job_queue_url = "";
    function handleGetQueueData(data) {
      log("handleGetQueueData: " + JSON.stringify(data));
      job_queue_url = data.QueueUrl;
      var params = {
        QueueUrl: job_queue_url,
        AttributeNames: ['All'],
        MaxNumberOfMessages: 1,
        VisibilityTimeout: 10,
        WaitTimeSeconds: 0
      };
      var response = sqs.receiveMessage(params);
      return response.promise();
    };

    var deleteParams = null;
    function handleProcessQueueData(response) {
      log("handleProcessQueueData: " + JSON.stringify(response));
      var msg = null;
      for(var idx in response.Messages) {
          msg = response.Messages[idx];
          deleteParams = {
            QueueUrl: job_queue_url,
            ReceiptHandle: msg.ReceiptHandle
          };
          log("handleProcessQueueData:  " + job_queue_url);
          return handleParseSQSBody(JSON.parse(msg.Body))
            .then(handleParseSQSMessage)
            .then(handleDeleteMessage);
      }
      log("handleProcessQueueData: no queued jobs available on " + job_queue_url);
      callback();
    };

    function handleDeleteMessage() {
      var promise = new Promise(function(resolve, reject){
          log(`handleDeleteMessage: ${JSON.stringify(deleteParams)}`);
          resolve(sqs.deleteMessage(deleteParams).promise());
      });
      return promise;
    }
    function handleParseSQSBody(body) {
      var promise = new Promise(function(resolve, reject){
          setTimeout(function() {
            log('handleParseSQSBody: ' + body);
            log('parse: ' + body.Message)
            resolve(JSON.parse(body.Message));
          }, 1000);
      });
      return promise;
    };
    /*
     * handleParseSQSMessage: {"Initialize":false,
     *    "Input":{},"Reset":false,
     *    "Simulation":"OUU","Visible":false,
     *    "Id":"4c797185-16a9-4b70-aea8-07d810475334"}
     */
    function handleParseSQSMessage(msg) {
      var promise = new Promise(function(resolve, reject){
          log('handleParseSQSMessage: ' + JSON.stringify(msg));
          if (msg.Simulation == 'OUU' || msg.Simulation == "zzfoqus_BFB") {
              var updates = [
                "[{\"status\": \"setup\", \"resource\": \"job\", \"rc\": 0, \"instanceid\": null, \"consumer\": \"00000000-0000-0000-0000-000000000000\", \"event\": \"status\", \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\"}]",
                "[{\"status\": \"running\", \"resource\": \"job\", \"rc\": 0, \"instanceid\": null, \"consumer\": \"00000000-0000-0000-0000-000000000000\", \"event\": \"status\", \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\"}]",
                "[{\"rc\": 0, \"resource\": \"job\", \"event\": \"output\", \"value\": \"DUMMY\", \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\"}]",
                "[{\"status\": \"success\", \"resource\": \"job\", \"rc\": 0, \"instanceid\": null, \"consumer\": \"00000000-0000-0000-0000-000000000000\", \"event\": \"status\", \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\"}]",
              ]
              var promises = [];
              for (var i in updates) {
                var obj = JSON.parse(updates[i]);
                obj[0].jobid = msg.Id;
                var message = JSON.stringify(obj);
                log(`publish(${update_topic_arn}): ${message}`);
                var event_description = obj[0].resource + "." + obj[0].event;
                if (obj[0].event == "status") {
                  event_description = obj[0].resource + "." + obj[0].status;
                }
                var params = {
                  Message: message,
                  MessageAttributes: {
                    'event': {
                      DataType: 'String',
                      StringValue: event_description
                    },
                  },
                  TopicArn: update_topic_arn,
                  Timeout: 2000*i
                };
                promises.push(promiseSNSPublish(params));
              }
              resolve(promises[0].then(promises[1]).then(promises[2]).then(promises[3]));
              //resolve(Promise.all(promises));
              //resolve(msg);
          } else {
              throw new Error(`Unsupported simulation "${msg.Simulation}"`);
          }
      });
      return promise;
    };

    function promiseSNSPublish(params) {
      var timeout = params["Timeout"];
      delete params["Timeout"];
      var promise = new Promise(function(resolve, reject){
          setTimeout(function() {
            log('handleSNSPublish: ' + JSON.stringify(params));
            var request = sns.publish(params);
            resolve(request.promise());
          }, timeout);
      });
      return promise;
    };

    function handleError(error) {
      log("handleError")
      if (error.name == "AWS.SimpleQueueService.NonExistentQueue") {
        log("NonExistentQueue: " + queue_name);
      } else {
        log(error, error.stack);
      }
      callback(error);
    };
};
