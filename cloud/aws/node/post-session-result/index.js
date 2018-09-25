/**
 * Lambda Function, returns a UUID for a new session resource
 * @module post-session-result
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
 'use strict';
 'use AWS.S3'
 'use AWS.DynamoDB'
 'use uuid'
const uuidv4 = require('uuid/v4');
const AWS = require('aws-sdk');
const default_user_name = "anonymous";
const s3_bucket_name = "foqus-sessions";
const tableName = "FOQUS_Resources";

// Returns page number
// session/{name}/result/{generator}
exports.handler = function(event, context, callback) {
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  /*
  if (event.httpMethod == "POST") {
      //var body = JSON.parse(event.body);
      var path  = event.path.split('/');
      var gen_id = path.pop();
      if (path.pop() != "result") {
        done(new Error(`Unsupported path "${event.path}"`));
      }
      var session_id = path.pop();

      callback(null, {statusCode:'200', body: "-1",
        headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
      });
  }
  */
  if (event.httpMethod == "POST") {
    var path  = event.path.split('/');
    var gen_id = path.pop();
    if (path.pop() != "result") {
      done(new Error(`Unsupported path "${event.path}"`));
    }
    var session_id = path.pop();
    var client = new AWS.S3();
    var dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
    /*
    dynamodb.query({ TableName: tableName,
        KeyConditionExpression: '#T = :job AND #C BEGINS_WITH :session',
        ExpressionAttributeNames: {"#T":"Type", "#C":"Composite"},
        ExpressionAttributeValues: { ":job":"Job", ":session":"SessionID="+session_id}
      },
      */
      dynamodb.query({ TableName: tableName,
          KeyConditionExpression: '#T = :job',
          ExpressionAttributeNames: {"#T":"Type"},
          ExpressionAttributeValues: { ":job":"Job", ":sessionid":session_id},
          FilterExpression: 'contains (SessionId, :sessionid)'
        },
        function(err,data) {
          var body = []
          if(err) {
            console.log("Error: ", err);
            callback(null, {statusCode:'400', body: JSON.stringify(data), headers: {'Content-Type': 'application/json',}});
          } else {
            // [{"Initialize":false,"Input":{},"Reset":false,
            //   "Simulation":"OUU","Visible":false,
            //   "Id":"448f3787-fead-47af-b32f-ba180c8e97ee"}]
            console.log('Data: ', data.Items.length);
            for (var i=0; i<data.Items.length; i++) {
                var item = data.Items[i];
                if (item.success != undefined) {
                  console.log('success item: ', item);
                  body.push({Id: item.Id,
                    Guid: item.Id,
                    Simulation: item.Simulation,
                    State: "success",
                    Messages: null,
                    Input: item.Input,
                    Output:item.output,
                    Session: item.SessionId,
                    Initialize: item.Initialize,
                    Reset:item.Reset,
                    Visible: false,
                    Input:item.Input,
                    Consumer: item.ConsumerId,
                    Create: item.Create,
                    Submit: item.Submit,
                    Setup: item.setup,
                    Running: item.running,
                    Finished: item.success});
                } else if (item.error != undefined) {
                  console.log('error item: ', item);
                  body.push({Id: item.Id,
                    Guid: item.Id,
                    Simulation: item.Simulation,
                    State: "error",
                    Messages: null,
                    Input: item.Input,
                    Output:item.output,
                    Session: item.SessionId,
                    Initialize: item.Initialize,
                    Reset:item.Reset,
                    Visible: false,
                    Input:item.Input,
                    Consumer: item.ConsumerId,
                    Create: item.Create,
                    Submit: item.Submit,
                    Setup: item.setup,
                    Running: item.running,
                    Finished: item.error});
                } else {
                  console.log('skip item: ', item);
                }
              }
              if (body.length == 0) {
                callback(null, {statusCode:'200', body: -1, headers: {'Content-Type': 'application/json',}});
                return;
              }

              var params = {
                Bucket: s3_bucket_name,
                Prefix: default_user_name + '/' + session_id + '/' + gen_id + '/',
              };

              client.listObjects(params, function(err, data) {
                if (err) console.log(err, err.stack); // an error occurred
                else {
                  var page = data.Contents.length + 1;
                  var content = JSON.stringify(body);
                  var params = {
                    Bucket: s3_bucket_name,
                    Key: default_user_name + '/' + session_id + '/' + gen_id + "/" + page + '.json',
                    Body: content
                  };
                  var request = client.putObject(params, function(err, data) {
                      console.log("putObject");
                      if (err) console.log(err, err.stack); // an error occurred
                      else     console.log("S3 PUTOBJECT")
                  });
                  callback(null, {statusCode:'200', body: page, headers: {'Content-Type': 'application/json',}});
                }
              });
            }
          }
        );
  }
  else {
      done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
};
