/**
 * Name:  post-session-append
 * Description: Add Array of jobs to a Session.  Uploads JSON Array of jobs
 * to S3 Session bucket with
 * key "s3://{SESSION_BUCKET_NAME}/user_name/milliseconds_since_epoch.json".
 * Next for each item in array a DynamoDB entry is made in FOQUS_Resources.
 *
 * @module post-session-append
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
'use AWS.DynamoDB'
'use uuid'
const log = require("debug")("post-session-append")
const AWS = require('aws-sdk');
//const s3 = require('s3');
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const uuidv4 = require('uuid/v4');
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const s3_sim_bucket_name = process.env.SIMULATION_BUCKET_NAME;
const tablename = process.env.FOQUS_DYNAMO_TABLE_NAME;


exports.handler = function(event, context, callback) {
    log(`Running index.handler: "${event.httpMethod}"`);

    if (event.requestContext == null) {
        context.fail("No requestContext for user mapping");
        callback(null, {statusCode:'500', body: "No requestContext for user mapping",
          headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
        });
        return;
    }
    if (event.requestContext.authorizer == null) {
        log("API Gateway Testing");
        var content = JSON.stringify([]);
        callback(null, {statusCode:'200', body: content,
          headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
        });
        return;
    }
    if (event.httpMethod != "POST") {
        context.fail(`Unsupported method "${event.httpMethod}"`);
        callback(null, {statusCode:'400', body: new Error(`Unsupported method "${event.httpMethod}"`),
          headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
        });
        return;
    }
    const s3 = new AWS.S3();
    const dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
    const user_name = event.requestContext.authorizer.principalId;
    const milliseconds = (new Date).getTime();
    const session_id = event.path.substring(event.path.lastIndexOf("/") + 1,
                        event.path.length);
    var id_list = [];
    var obj = null;
    function parseBodyJSON() {
        var promise = new Promise(function(resolve, reject){
            log('parseBodyJSON');
            obj = JSON.parse(event.body);
            for (var i=0; i<obj.length; i++) {
                obj[i].Id = uuidv4();
            }
            resolve(obj);
        });
        return promise;
    };
    function validateJobs(job_array) {
      var promise = new Promise(function(resolve, reject){
          log(`validateJobs items: ${job_array.length}`);
          for (var i=0; i<job_array.length; i++) {
            if(!job_array[i].Simulation) {
                throw new Error(`append validate job failed (index=${i}):  Simulation not specified`)
            }
            if(!job_array[i].Input) {
                throw new Error(`append validate job failed (index=${i}):  Input not specified`)
            }
          }
          resolve(job_array);
      });
      return promise;
    }
    function writeToDynamo(job_array) {
        log(`writeToDynamo:  count=${job_array.length}`);
        var items = [];
        var params = {
          RequestItems: {
        }};
        params["RequestItems"][tablename] = items;
        var item = null;
        var i = 0;
        for(var i=0; i<job_array.length; i++) {
          var d = new Date(milliseconds+i);
          id_list.push(job_array[i].Id);
          item = {Id: job_array[i].Id,
                  Type: "Job",
                  State: "create",
                  Create: d.toISOString(),
                  SessionId: session_id,
                  User: user_name,
                  Initialize: job_array[i].Initialize,
                  Input: job_array[i].Input,
                  Reset:job_array[i].Reset,
                  TTL: Math.floor(Date.now()/1000 + 60*60*12),
                  Simulation: job_array[i].Simulation,
                  Application: job_array[i].Application || "foqus"};

          items.push({PutRequest: { Item: item } });
        }
        log(`Dynamodb.batchWrite to ${tablename}`);
        var response = dynamodb.batchWrite(params);
        return response.promise().then(checkForUnprocessedItems);
    };
    function checkForUnprocessedItems(response) {
        log(`checkForUnprocessedItems: ${JSON.stringify(response)}`);
        if (Object.keys(response.UnprocessedItems).length == 0) {
          log("Zero UnprocessedItems")
          return;
        }
        var params = {
          RequestItems: {
        }};
        params["RequestItems"][tablename] = response.UnprocessedItems;
        log(`Dynamodb.batchWrite to ${tablename}`);
        var response = dynamodb.batchWrite(params);
        return response.promise().then(checkForUnprocessedItems);
    }
    function putS3() {
        // NOTE: using curried variable to access JSON request
        // set in dynamo function.  Like to turn this into a
        // parameter
        var job_array = obj;
        var promise = new Promise(function(resolve, reject){
            log(`putS3 items: ${job_array.length}`);
            var content = JSON.stringify(job_array);
            if(content == undefined) {
                throw new Error("s3 object is undefined")
            }
            if(content.length == undefined) {
                throw new Error("s3 object is empty")
            }
            var params = {
              Bucket: s3_bucket_name,
              Key: user_name + '/session/create/' + session_id + '/' + milliseconds + '.json',
              Body: content
            };
            log(`putS3(${params.Bucket}):  ${params.Key}`);
            var request = s3.putObject(params);
            resolve(request.promise());
        });
        return promise;
    };
    function handleError(error) {
      log(`handleError ${error.name}`);
      callback(null, {statusCode:'400',  body: `Failed to append jobs: ${error}`,
        headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
      });
    };
    function handleDone() {
        log("handleDone");
        callback(null, {statusCode:'200', body: JSON.stringify(id_list),
          headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
        });
    }
    var promise = parseBodyJSON(event);
    promise.then(validateJobs)
      .then(writeToDynamo)
      .then(putS3)
      .then(handleDone)
      .catch(handleError);
};
