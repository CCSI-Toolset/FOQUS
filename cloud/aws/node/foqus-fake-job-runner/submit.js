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
'use uuid'
const AWS = require('aws-sdk');
const sqs = new AWS.SQS();
const sns = new AWS.SNS();
const queue_name = process.env.FOQUS_JOB_QUEUE;
const update_topic_arn = process.env.FOQUS_UPDATE_TOPIC_ARN;
//const log = require("debug")("foqus-fake-job-runner")

console.log('foqus-fake-job-runner loading submit');

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
    console.log(JSON.stringify(event));
    for (const { messageId, body } of event.Records) {
        console.log('SQS message %s: %j', messageId, body);
        var job = JSON.parse(body);
        console.log('job submit: %j', job);
        if (job.resource != "job") {
          console.log(`"ignore message: resource=${job.resource} ${messageId}"`);
          continue;
        }
        if (job.status != "submit") {
          console.log(`"ignore message: status=${job.status} messageid=${messageId}"`);
          continue;
        }
        // MOVE JOB submit -> setup
        var job_setup = JSON.parse("{}");
        job_setup.resource = "job";
        job_setup.event = "status";
        job_setup.status = "setup";
        job_setup.jobid = job.jobid;
        job_setup.instanceid = job.instanceid;
        job_setup.consumer = "00000000-0000-0000-0000-000000000000";
        job_setup.sessionid = job.sessionid;

        job_setup.Initialize = job.Initialize;
        job_setup.Input = job.Input;
        job_setup.Reset = job.Reset;
        job_setup.Simulation = job.Simulation;
        job_setup.Visible = job.Visible;

        var params = {
          Message: JSON.stringify(job_setup),
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
