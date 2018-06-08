'use strict';
'use AWS.DynamoDB'

// https://github.com/motdotla/node-lambda-template
// NOTE:  CORS For Integrated Lambda Proxy Must be done in Lambda functions
//  because "Integration Response" is disabled, CORS settings will not work!
//  Follow the link:
//     https://stackoverflow.com/questions/40149788/aws-api-gateway-cors-ok-for-options-fail-for-post
//
console.log('Loading function');
const AWS = require('aws-sdk');
const tableName = "FOQUS_Resources"
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
            console.log('Data: ', data.Items.length);
            for (var i=0; i<data.Items.length; i++) {
                var item = data.Items[i];
                if (item.SessionId == session_id) {
                  console.log('item: ', item);
                  body.push({Id: item.Id,
                    Application: item.Application,
                    SessionId: item.SessionId,
                    Initialize: item.Initialize,
                    Input:item.Input,
                    Reset:item.Reset,
                    Simulation: item.Simulation,
                    Output:item.Output});
                }
              }
              callback(null, {statusCode:'200', body: JSON.stringify(body), headers: {'Content-Type': 'application/json',}});
           }
      });
  }

  console.log('==================================');
  console.log('Stopping index.handler');
};
