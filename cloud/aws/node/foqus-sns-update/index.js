'use strict';
'use AWS.S3'
'use AWS.DynamoDB'
'use uuid'
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
const tablename = 'TurbineResources';

var process_job_event = function(ts, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
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
        //ExpressionAttributeNames:{
        //    "#t":"Type"
        //},
        ReturnValues:"UPDATED_NEW"
    };
    console.log("job(msecs=" + msecs + ") event=" + e);
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

var process_consumer_event = function(ts, message, callback) {
    // ts -- "Timestamp": "2018-05-10T01:47:26.794Z",
    var e = message['event'];
    var msecs = Date.parse(ts);
    console.log("consumer(msecs=" + msecs + ") event=" + e);
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
