/**
 * Pops job off SQS Job queue and sends canned notifications to SNS Update Topic
 * which will cause foqus-sns-update to create job updates.
 *
 * @module foqus-fake-job-runner
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
const AWS = require('aws-sdk');
const sqs = new AWS.SQS();
const sns = new AWS.SNS();
const queue_name = process.env.FOQUS_JOB_QUEUE;
const update_topic_arn = process.env.FOQUS_UPDATE_TOPIC_ARN;
const s3_bucket_name = process.env.SIMULATION_BUCKET_NAME;
//const log = require("debug")("foqus-fake-job-runner")

console.log('foqus-fake-job-runner loading setup');

/*
 * {\"Initialize\":false,\"Input\":{},\"Reset\":false,\"Simulation\":\"OUU\",
 * \"Visible\":false,\"Id\":\"0c8d3e01-030c-45e4-b579-c3f5dad026a0\",
 * \"resource\":\"job\",\"status\":\"submit\",
 * \"jobid\":\"0c8d3e01-030c-45e4-b579-c3f5dad026a0\",
 * \"sessionid\":\"80a19bc7-728e-45cd-bddd-331420955cfa\",\"event\":\"status\"}
 */

// d = dict(
//      resource="job",
//      event="status",
//      rc=rc,
//      status=status,
//      jobid=job_d["Id"],
//      instanceid=_instanceid,
//      consumer=self.consumer_id,
//      sessionid=job_d.get("sessionid", "unknown"),
//  )
//  if message:
//      d["message"] = message

exports.handler = async (event) => {
    let promises = [];
    function handleDone() {
      console.log("handleDone");
      return 1;
    };
    function handleError(error) {
      console.log(`handleError ${error}`);
      return 0;
    };
    console.log(JSON.stringify(event));
    for (const { Sns } of event.Records) {
        var messageId = Sns.MessageId;
        var user_name = Sns.MessageAttributes.username.Value;
        var application = Sns.MessageAttributes.application.Value;
        var body = Sns.Message;
        console.log('SQS message %s: %j', messageId, body);
        var job = JSON.parse(body);
        console.log('job setup: %j', job);
        if (job.resource != "job") {
          console.log(`"ignore message: resource=${job.resource} ${messageId}"`);
          continue;
        }
        if (job.status != "setup") {
          console.log(`"ignore message: status=${job.status} messageid=${messageId}"`);
          continue;
        }
        // MOVE JOB setup -> running
        var job_run = JSON.parse("{}");
        job_run.resource = "job";
        job_run.event = "status";
        job_run.status = "running";
        job_run.jobid = job.jobid;
        job_run.instanceid = job.instanceid;
        job_run.consumer = job.consumer;
        job_run.sessionid = job.sessionid;

        job_run.Initialize = job.Initialize;
        job_run.Input = job.Input;
        job_run.Reset = job.Reset;
        job_run.Simulation = job.Simulation;
        job_run.Visible = job.Visible;

        function handleS3Error(error) {
          console.log(`handleS3Error ${error.name}`);
          job_run.status = "error";
          job_run.message = `AWS.S3 ${error.name}: Simulation Not Found`;
          var promise = new Promise(function(resolve, reject){
            //resolve(request.promise());
            var obj = new Object();
            obj.Body = "{}";
            resolve(obj);
          });
          return promise;
        };
        function publishSNS(s3_file_response) {
            // NOTE: using curried variable to access JSON request
            // set in dynamo function.  Like to turn this into a
            // parameter
            console.log("S3 DATA");
            console.log(s3_file_response);
            var meta_obj = JSON.parse(s3_file_response.Body);
            console.log(JSON.stringify(meta_obj));
            var promise = new Promise(function(resolve, reject){
              var params = {
                Message: JSON.stringify(job_run),
                MessageAttributes: {
                  'event': {
                    DataType: 'String',
                    StringValue: `job.${job_run.status}`
                  },
                  'username': {
                    DataType: 'String',
                    StringValue: user_name
                  },
                  'application': {
                    DataType: 'String',
                    StringValue: application
                  }
                },
                TopicArn: update_topic_arn
              };
              console.log(`SNS Publish: ${JSON.stringify(params)}`);
              var request = sns.publish(params);
              resolve(request.promise());
            });
            return promise;
        };
        // CHECK FOR SIMULATION
        var client = new AWS.S3();
        var params = {
          Bucket: s3_bucket_name,
          Key: user_name + "/" + job.Simulation + "/meta.json"
        };
        var response = client.getObject(params);
        var promise = response.promise()
          .catch(handleS3Error)
          .then(publishSNS)
          .then(handleDone);
        promises.push(promise);
    }
    return Promise.all(promises);
};
