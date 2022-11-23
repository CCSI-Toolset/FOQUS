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
//const log = require("debug")("foqus-fake-job-runner")

console.log('foqus-fake-job-runner loading function');

/*
 * {\"Initialize\":false,\"Input\":{},\"Reset\":false,\"Simulation\":\"OUU\",
 * \"Visible\":false,\"Id\":\"0c8d3e01-030c-45e4-b579-c3f5dad026a0\",
 * \"resource\":\"job\",\"status\":\"submit\",
 * \"jobid\":\"0c8d3e01-030c-45e4-b579-c3f5dad026a0\",
 * \"sessionid\":\"80a19bc7-728e-45cd-bddd-331420955cfa\",\"event\":\"status\"}
 */
exports.handler = async (event) => {
    let promises = [];
    console.log(JSON.stringify(event));
    for (const { messageId, body } of event.Records) {
        console.log('SQS message %s: %j', messageId, body);
        var job = JSON.parse(body);
        console.log('job submit: %j', job);
        console.log('job submit: %j', job.status);
        if (job.status == "submit") {
            job.status = "setup";
        } else {
          console.log(`"ignore message ${messageId}"`);
          continue;
        }
        job.consumer = "00000000-0000-0000-0000-000000000000";
        var params = {
          Message: JSON.stringify(job),
          MessageAttributes: {
            'event': {
              DataType: 'String',
              StringValue: "job.setup"
            },
            'username': {
              DataType: 'String',
              StringValue: "boverhof"
            },
            'application': {
              DataType: 'String',
              StringValue: "fake-job"
            }
          },
          TopicArn: update_topic_arn
        };
        //"[{\"resource\": \"job\", \"event\": \"status\", \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\",
        //\"status\": \"setup\", \"rc\": 0, \"instanceid\": null, \"consumer\": \"00000000-0000-0000-0000-000000000000\"}]"
        var promise = sns.publish(params).promise();
        promises.push(promise);
    }
    return Promise.all(promises);
};
