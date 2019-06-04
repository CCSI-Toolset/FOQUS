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
const log = require("debug")("post-session-result")
const uuidv4 = require('uuid/v4');
const AWS = require('aws-sdk');
const tableName = process.env.FOQUS_DYNAMO_TABLE_NAME;
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;


function push_finished_job(item, body) {
  if (item.success != undefined) {
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
  }
  if (item.error != undefined) {
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
    }
}

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
      return;
    }
    const user_name = event.requestContext.authorizer.principalId;
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
          var body = [];
          var unfinished_jobs = {};
          var finished_jobs = {};
          if(err) {
            log("Error: ", err);
            callback(null, {statusCode:'400', body: JSON.stringify(data), headers: {'Content-Type': 'application/json',}});
          } else {
            // [{"Initialize":false,"Input":{},"Reset":false,
            //   "Simulation":"OUU","Visible":false,
            //   "Id":"448f3787-fead-47af-b32f-ba180c8e97ee"}]
            log(`Data(Session=${session_id}): ${data.Items.length}`);
            for (var i=0; i<data.Items.length; i++) {
                var item = data.Items[i];
                if (item.success != undefined && item.output != undefined) {
                  log('success item: ', item);
                  finished_jobs[item.Id] = item;
                } else if (item.error != undefined) {
                  log('error item: ', item);
                  finished_jobs[item.Id] = item;
                } else {
                  log('unfinished item: ', item);
                  unfinished_jobs[item.Id] = item;
                }
              }
              var finished_ids = Object.keys(finished_jobs);
              var unfinished_ids = Object.keys(unfinished_jobs);
              if (finished_ids.length== 0) {
                if (unfinished_ids.length == 0)
                  callback(null, {statusCode:'200', body: 0, headers: {'Content-Type': 'application/json',}});
                else
                  callback(null, {statusCode:'200', body: -1, headers: {'Content-Type': 'application/json',}});
                return;
              }

              var params = {
                Bucket: s3_bucket_name,
                MaxKeys: 1000,
                Prefix: user_name + '/' + session_id + '/' + gen_id + '/page/',
              };

              // NOTE: Max 1000 Keys returned by this response
              client.listObjects(params, function(err, data) {
                log("==> LIST OBJECTS: " + data.Contents.length);
                if (err) {
                  log(err, err.stack); // an error occurred
                  done(new Error(err));
                  return;
                }
                if (data.Contents == 1000) {
                  log("Not Implemented: FOUND MaxKeys 1000");
                  done(new Error("Not Implemented: FOUND MaxKeys 1000"));
                  return;
                }
                var results_set = new Set();
                var next_page_number = 0;
                // {user_name}/{session_id}/{generation_id}/page/{number}/{id}.json
                var regex = user_name + '/' + session_id + '/' + gen_id + '/page/(\\d+)/([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\.json$';
                log("REGEX: " + regex);
                for (var i=0; i<data.Contents.length; i++) {
                  var item = data.Contents[i];
                  log("ITEM:  " + item.Key);
                  var match = item.Key.match(regex);
                  if (match) {
                    // anonymous/90e35450-4460-4f55-a3ad-4423b8f16816/27849bcb-18aa-467c-9ad8-2252ea0a3182/page/1/3f05cf85-f891-4e94-a97d-fd90c20e6d17.json
                    log("PAGE NUMBER: " + match[1]);
                    log("UUID MATCH: " + match[2]);
                    var num = parseInt(match[1]);
                    if (next_page_number < num) next_page_number = num;
                    var job_id = match[2];
                    results_set.add(job_id);
                  } else {
                    log("==> NO MATCH");
                  }
                }

                log("results_set.length " + results_set.size );
                log("finished_ids.length " + finished_ids.length);
                if (results_set.size == finished_ids.length) {
                  callback(null, {statusCode:'200', body: 0, headers: {'Content-Type': 'application/json',}});
                  return;
                }
                if (results_set.size > finished_ids.length) {
                  done(new Error("Data Error: More jobs in S3 than in DynamoDB"));
                  return;
                }

                next_page_number += 1;
                for (var key in finished_jobs) {
                  if (results_set.has(key) == false) {
                    push_finished_job(finished_jobs[key], body);
                  }
                }
                for (var i=0; i<body.length; i++) {
                  var params = {
                    Bucket: s3_bucket_name,
                    Key: user_name + '/' + session_id + '/' + gen_id + "/page/" + next_page_number + '/' + body[i].Id + '.json',
                    Body: JSON.stringify(body[i])
                  };
                  client.putObject(params, function(err, data) {
                      log("putObject: " + params.Key);
                      if (err) {
                        log(err, err.stack); // an error occurred
                      }
                  });
                }
                var content = JSON.stringify(body);
                var params = {
                  Bucket: s3_bucket_name,
                  Key: user_name + '/' + session_id + '/' + gen_id + "/" + next_page_number + '.json',
                  Body: content
                };

                var request = client.putObject(params, function(err, data) {
                    log("putObject: " + params.Key);
                    if (err) {
                      log(err, err.stack); // an error occurred
                      done(new Error(err));
                      return;
                    }
                    callback(null, {statusCode:'200', body: next_page_number,
                      headers: {'Content-Type': 'application/json',}});
                });

              });
            }
          }
        );
  }
  else {
      done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
};
