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
//const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
//const tablename = 'FOQUS_Resources';
const sqs = new AWS.SQS();
const sns = new AWS.SNS();

var publish_job_updates = function(message) {
  /* { MessageId: '1f811f27-fd27-4d13-b1a4-85f7adead4c6',
       ReceiptHandle: 'AQEB1q2ZIZ4UEsnFiVN+DOqvgvQvAxPx0qzAxQ6vg93p23XYhB34oRVJcf7NdztezonVVgMH+EApkjN8OYq7oUByd3gxveYhOr+EzBKFObnPwFkK11KG5L1u7QYrEKbn8Bxq8+UWL0WEoDpFNO4fb1HbIOiLBl/D5HsfnnvaRGiKSjbYC+oRejSqIkx005USbMcCQrzbM3kmfiRHBxM2iD4vMsmgYWtOBigF8ZMf4iIbMiUrwCbPUWIHrvNSfs8z0ldEsNruymMbEFUJ00eqIZlPJdVl2YCi1Ve4fKZn1Sbsm+hzV7VPxEIZwbULXigeKO9dRL2mJT9hmBOn4HLM6v2/udkDhJHcDp9jLtz2tJZ4tSTwPwKe9CloXBDWgNanoKcE8PthgSK5M/YgznscntCZMw==',
       MD5OfBody: '689dde5570fcd38a36712a9309cf4913',
       Body: '{\n  "Type" : "Notification",\n  "MessageId" : "5afbc948-e910-559f-9715-9a822554a7bf",\n
       "TopicArn" : "arn:aws:sns:us-east-1:754323349409:FOQUS-Job-Topic",\n
       "Message" : "{\\"Reset\\":false,\\"Input\\":{\\"graph\\":{},\\"BFB\\":{\\"BFBadsB.Dt\\":11.897,\\"BFBadsB.dx\\":0.0127,\\"BFBadsB.Lb\\":2.085,\\"BFBadsM.Dt\\":15,\\"BFBadsM.dx\\":0.06695,\\"BFBadsM.Lb\\":1.972,\\"BFBadsT.Dt\\":15,\\"BFBadsT.dx\\":0.062397,\\"BFBadsT.Lb\\":2.203,\\"BFBRGN.Dt\\":9.041,\\"BFBRGN.Lb\\":8.886,\\"BFBRGNTop.Dt\\":9.195,\\"BFBRGNTop.Lb\\":7.1926,\\"GHXfg.A_exch\\":16358,\\"Kd\\":100,\\"BFBadsB.Cr\\":1,\\"BFBadsM.Cr\\":1,\\"BFBadsT.Cr\\":1,\\"BFBRGN.Cr\\":1,\\"BFBRGNTop.Cr\\":1,\\"dp\\":0.00015,\\"GHXfg.GasIn.P\\":1.01325,\\"GHXfg.GasIn.T\\":54,\\"fg_flow\\":100377}},\\"Simulation\\":\\"zzfoqus_BFB\\",\\"Id\\":\\"3494e851-3304-4a41-be47-44083108083b\\"}",\n  "Timestamp" : "2018-07-19T17:27:32.471Z",\n
       "SignatureVersion" : "1",\n
       "Signature" : "E3AtjWqp/TrEDboKJDTJi+6FBpFhCKBp1MbfWu2ssgFmnKk9RVU5yjxTCPGStwR1vrqErNW9xjFHnptEx8O3q1HwAZ5Bq65kl/he8g7/C6gXzuYwCfywGLMNX1SiMR34qb5nfY3WXRAjN5GONjTT8Pa9ZmXbpGNkjDKDfIQ55ESnU24eRIecfX+X4hdhpJQUBa9rBrivHEEfLurw8jQnG0yF95s2BYFiOOH6L8obU5LC2iLYR9qH2fls+8GmN2EoYTPhx+QF4giOvnvYhdDLoCqc9u/+uqyMndL9KevicBdGR2dT6FpUYD6dFfTjs/Rli7ZD//v9BTWn35U2YGXQvA==",\n
       "SigningCertURL" : "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-eaea6120e66ea12e88dcd8bcbddca752.pem",\n  "UnsubscribeURL" : "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:754323349409:FOQUS-Job-Topic:a77d42ea-3849-4fc3-bbcd-da0f0a157dcc"\n}',
       Attributes: [Object] } ]
   */
   var job_request = JSON.parse(message.Body);
   job_request = JSON.parse(job_request.Message);
   console.log("FOUND JOB: " +  job_request.Id);
   var updates = [
     "[{\"status\": \"setup\", \"resource\": \"job\", \"rc\": 0, \"instanceid\": null, \"consumer\": \"b5dd83d8-3762-470d-9ba1-34ce6f0e753d\", \"event\": \"status\", \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\"}]",
     "[{\"status\": \"running\", \"resource\": \"job\", \"rc\": 0, \"instanceid\": null, \"consumer\": \"b5dd83d8-3762-470d-9ba1-34ce6f0e753d\", \"event\": \"status\", \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\"}]",
     "[{\"rc\": 0, \"resource\": \"job\", \"event\": \"output\", \"value\": {\"input\": {\"graph\": {}, \"BFB\": {\"BFBadsT.dx\": 0.062397, \"BFBadsT.Lb\": 2.203, \"BFBadsB.Cr\": 1.0, \"BFBRGN.Dt\": 9.041, \"GHXfg.GasIn.T\": 54.0, \"GHXfg.A_exch\": 16358.0, \"BFBadsM.Dt\": 15.0, \"BFBadsB.dx\": 0.0127, \"BFBadsT.Dt\": 15.0, \"BFBadsM.Lb\": 1.972, \"BFBRGN.Lb\": 8.886, \"BFBRGNTop.Dt\": 9.195, \"GHXfg.GasIn.P\": 1.01325, \"Kd\": 100.0, \"BFBadsB.Dt\": 11.897, \"BFBadsM.dx\": 0.06695, \"BFBRGN.Cr\": 1.0, \"BFBRGNTop.Lb\": 7.1926, \"fg_flow\": 100377.0, \"dp\": 0.00015, \"BFBadsT.Cr\": 1.0, \"BFBRGNTop.Cr\": 1.0, \"BFBadsM.Cr\": 1.0, \"BFBadsB.Lb\": 2.085}}, \"nodeError\": {\"BFB\": 0}, \"nodeSettings\": {\"BFB\": {\"Reset\": false, \"Maximum Run Time (s)\": 840.0, \"Retry\": false, \"TimeSeries\": [0.0], \"Script\": \"\", \"TimeUnits\": \"Hours\", \"Allow Simulation Warnings\": true, \"homotopy\": 0, \"Min Status Check Interval\": 4.0, \"RunMode\": \"Steady State\", \"Snapshot\": \"\", \"Initialize Model\": false, \"Max Status Check Interval\": 5.0, \"printlevel\": 0, \"Reset on Fail\": true, \"Maximum Wait Time (s)\": 1440.0, \"Visible\": false, \"Max consumer reuse\": 90, \"Override Turbine Configuration\": \"\", \"MinStepSize\": 0.001}}, \"output\": {\"graph\": {\"error\": 0.0}, \"BFB\": {\"removalCO2\": 0.8999964373466817, \"removalCO2_slack\": 0.0, \"SHX.SteamFR\": 37683.43278161038, \"slugam_slack\": 0.0, \"GHXfg.HXIn.F\": 135788.8395015208, \"slugrb_slack\": 0.0, \"Cost_op_fixed\": 54526718.57072218, \"BFBRGN.GasIn.F\": 1357.0814214980398, \"Cost_ads\": 34830765.96283022, \"Cost_steam_power\": 179203.44430650023, \"SHX.RichIn.T\": 83.99312572585319, \"SHX.CWFR\": 26890.328479471482, \"slugab_slack\": 0.0, \"Cost_op_cooling_water\": 12577963.846287617, \"Cost_toc_sorb\": 83874472.31479213, \"Cost_rgn\": 16321781.413333291, \"status\": 0.0, \"SHX.RichOut.T\": 170.0, \"slugrt_slack\": 0.0, \"Cost_toc\": 2111440309.1504824, \"F_solids\": 12681737.021801885, \"Cost_shx\": 39020395.75661277, \"Cost_coe_obj\": 138.85964658190665, \"Cost_aux_power\": 23378.969592384507, \"Cost_op_var\": 172437413.51951027, \"Cost_op_cooling_water_flow\": 2927442.0442882474, \"SHX.LeanIn.T\": 146.3820219819483, \"SHX.LeanOut.T\": 70.57864346590641, \"Cost_steam_tot\": 696035.1169336186, \"slugat_slack\": 0.0, \"Cost_coe\": 138.85964658190665}}, \"turbineMessages\": {\"BFB\": \"\"}, \"graphError\": 0, \"solTime\": 98.46600008010864}, \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\"}]",
     "[{\"status\": \"success\", \"resource\": \"job\", \"rc\": 0, \"instanceid\": null, \"consumer\": \"b5dd83d8-3762-470d-9ba1-34ce6f0e753d\", \"event\": \"status\", \"jobid\": \"3494e851-3304-4a41-be47-44083108083b\"}]",
   ]

   for (var i=0; i<updates.length; i++) {
     var obj = JSON.parse(updates[i]);
     obj[0].jobid = job_request.Id;
     var message = JSON.stringify(obj);
     console.log("publish: " + message);
     var params = {
       Message: message,
       TopicArn: 'arn:aws:sns:us-east-1:754323349409:FOQUS-Update-Topic'
     };
     //console.log("publish: " +  updates[i]);
     sns.publish(params, function(err, data) {
       if (err) console.log(err, err.stack); // an error occurred
       else     console.log(data);           // successful response
     });
   }
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
    var params = {
      QueueUrl: 'https://sqs.us-east-1.amazonaws.com/754323349409/FOQUS-Job-Queue', /* required */
      AttributeNames: [
        'All'
      ],
      MaxNumberOfMessages: 1,
      VisibilityTimeout: 10,
      WaitTimeSeconds: 0
    };
    sqs.receiveMessage(params, function(err, data) {
      if (err) console.log(err, err.stack); // an error occurred
      else  {
        console.log(data);
        if (data.Messages == undefined) return;
        if (data.Messages.length == 1) {
          console.log("FOUND ONE SEND JOB CHANGE UPDATES");
          publish_job_updates(data.Messages[0]);
        }

      }
    });

};
