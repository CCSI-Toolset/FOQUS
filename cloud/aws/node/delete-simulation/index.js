'use strict';
'use AWS.DynamoDB'
console.log('Loading function');
const AWS = require('aws-sdk');
const uuidv4 = require('uuid/v4');
var validate = require('uuid-validate');

/*
 * new-simulation
 */
exports.handler = function(event, context, callback) {
  console.log('Running get-simulation index.handler');
  console.log('==================================');
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  var tableName = "TurbineResources";
  var dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
  if (event.httpMethod == "DELETE") {
      var path_array = event.path.split('/');
      var resource_id = path_array[path_array.length-1];
      var params = null;
      console.log('PUT RESOURCE: ', resource_id);
      if (validate(resource_id) ) {
        //var params = {TableName: tableName};
        //params.Key = {Id:resource_id,Type:"Simulation"};
        params = { TableName: tableName,
            Key: {
              'Type':'Simulation',
              'Id':resource_id
            },
            ReturnValues: "ALL_OLD"
          };
          dynamodb.delete(params,
            function(err,data) {
              if(err) {
                console.log("Error: ", err);
                callback(null, {statusCode:'400', body: JSON.stringify(data),
                  headers: {'Content-Type': 'application/json',}});
              } else {
                console.log('Data: ', data);
                var content = JSON.stringify(data);
                callback(null, {statusCode:'200', body: content,
                  headers: {'Content-Type': 'application/json',}});
              }
          });
      } else {
        callback(null, {statusCode:'500',
            body: "Delete only supports Id, not names currently",
            headers: {'Content-Type': 'application/json',}});
      }
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  console.log('==================================');
  console.log('Stopping index.handler');
};
