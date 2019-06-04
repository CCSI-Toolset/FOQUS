/**
 * Lambda Function, returns an Array of jobs in the Session specified.
 * @module get-session
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.DynamoDB'
console.log('Loading function');
const AWS = require('aws-sdk');
const tableName = process.env.FOQUS_DYNAMO_TABLE_NAME;

// For development/testing purposes
exports.handler = function(event, context, callback) {
  console.log(`Running index.handler: "${event.httpMethod}"`);
  console.log("request: " + JSON.stringify(event));
  console.log('==================================');
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  if (event.httpMethod == "GET") {
    var session_id = event.path.substring(event.path.lastIndexOf("/") + 1,
                        event.path.length);
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

            /* states = set(['submit', 'create', 'setup', 'running', 'success', 'warning',
              'error', 'expired', 'cancel', 'terminate', 'pause'])
             */
            console.log('Data: ', data.Items.length);
            for (var i=0; i<data.Items.length; i++) {
                var item = data.Items[i];
                if (item.SessionId == session_id) {
                  console.log('item: ', item);
                  var obj =  {Id: item.Id,
                    Application: item.Application,
                    SessionId: item.SessionId,
                    Initialize: item.Initialize,
                    Input:item.Input,
                    State:"create",
                    Reset:item.Reset,
                    Simulation: item.Simulation,
                    Create: item.Create,
                    Output:item.Output}
                  if (item.submit) {
                    obj.Submit = item.submit;
                    obj.State = "submit";
                  }
                  if (item.setup) {
                    obj.Setup = item.setup;
                    obj.State = "setup";
                  }
                  if (item.running) {
                    obj.Running = item.running;
                    obj.State = "running";
                  }
                  if (item.success) {
                    obj.Finished = item.success;
                    obj.State = "success";
                  }
                  if (item.error) {
                    obj.Finished = item.error;
                    obj.State = "error";
                  }
                  body.push(obj);
                }
              }
              callback(null, {statusCode:'200', body: JSON.stringify(body), headers: {'Content-Type': 'application/json',}});
           }
      });
  }

  console.log('==================================');
  console.log('Stopping index.handler');
};
