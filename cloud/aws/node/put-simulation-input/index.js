/**
 * Lambda Function, attempts to upload to HTTP Body to S3 Simulation Bucket
 * Returns:
 * - HTTP 413 Payload Too Large
 * - HTTP 200 Success
 * @module put-simulation-input
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
const AWS = require('aws-sdk');
const log = require("debug")("put-simulation-input")
const fs = require('fs');
const dirPath = "./tmp";
const path = require('path');
const abspath = path.resolve(dirPath);
const s3_bucket_name = process.env.SIMULATION_BUCKET_NAME;


exports.handler = function(event, context, callback) {
  log(`Running index.handler: "${event.httpMethod}"`);
  log("event: " + JSON.stringify(event));
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });

  if (event.requestContext == null) {
    context.fail("No requestContext for user mapping")
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
  const user_name = event.requestContext.authorizer.principalId;
  if (event.httpMethod == "PUT" ) {
    var array = event.path.split('/');
    var item = array.pop();
    var key = null;

    if (item == "input") {
      done(new Error(`Unsupported path "${event.path}"`));
      return;
    }

    while (item != "input") {
      if (key == null) {
        key = item;
      }
      else {
        key = item + "/" + key;
      }
      item = array.pop();
    }
    //var resource = array.pop();
    // simulation/{name}/input/{file_path}
    if (item != "input") {
      done(new Error(`Unsupported path "${event.path}"`));
      return;
    }
    var name = array.pop();
    if (array.pop() != "simulation") {
      done(new Error(`Unsupported path "${event.path}"`));
      return;
    }

    var params = {
      Bucket: s3_bucket_name,
    };

    if (event.queryStringParameters && event.queryStringParameters.SignedUrl) {
      // if (key == "configuration") {
      //   log("queryStringParameters SignedUrl: unsupported for configuration files");
      //   callback(null, {statusCode:'406', body:'SignedUrl unsupported for configuration files',
      //         headers: {'Access-Control-Allow-Origin': '*', 'Content-Type': 'text/plain'}
      //       });
      //   return;
      // }
      // if (key == 'aspenfile') {
      //   log("aspenfile resource unsupported, PUT as filename directly");
      //   callback(null, {statusCode:'406', body:'aspenfile resource unsupported, PUT as filename directly',
      //         headers: {'Access-Control-Allow-Origin': '*', 'Content-Type': 'text/plain'}
      //       });
      //   return;
      // }
      // params.Expires = 120;
      // params.Key = `${user_name}/${name}/${key}`;
      // //params.ContentType = 'application/json';
      // log("Body is null, return HTTP 302 with S3 Signed URL for Large Files");
      // var s3 = new AWS.S3();
      // var url = s3.getSignedUrl('putObject', params);
      // log("S3 SignedURL: " + url);
      // //var obj = {"SignedUrl":url};
      // callback(null, {statusCode:'302',
      //       headers: {'Access-Control-Allow-Origin': '*',
      //         'Location': url }
      //     });
      // return;
      done(new Error(`PUT SignedUrl no longer supported "${event.path}"`));
      return;
    }

    params.Body = event.body;
    if (key == "configuration") {
      var obj = null;
      try {
        obj = JSON.parse(event.body);
      } catch(e) {
        done(new Error(`Failed to parse as JSON`));
        return;
      }
      if (obj.filetype == "sinterconfig" && obj.aspenfile != undefined) {
        if (obj.aspenfile.endsWith('.acmf'))
          params.Key = user_name + "/" + name + "/acm_sinter.json";
        else if (obj.aspenfile.endsWith('.bkp'))
          params.Key = user_name + "/" + name + "/aspenplus_sinter.json";
        else {
          log(event.body);
          done(new Error(`Inspection sinterconfig v0.1 failed to identify configuration file type`));
          return;
        }
      }
      else if (obj.filetype == "sinterconfig" && obj["config-version"] == "0.2") {
        if (obj.model.file.endsWith('.acmf'))
          params.Key = user_name + "/" + name + "/acm_sinter.json";
        else if (obj.model.file.endsWith('.bkp'))
          params.Key = user_name + "/" + name + "/aspenplus_sinter.json";
        else {
          log(event.body);
          done(new Error(`Inspection sinter config v0.2 failed to identify configuration file type`));
          return;
        }
      }
      else if (obj.filetype == "sinterconfig" && obj["filetype-version"] == "0.3") {
        var app_name = obj.application.name;
        app_name = app_name.toLowerCase();
        if (obj.model.file.endsWith('.py') && app_name == "foqus-user-plugin")
          params.Key = user_name + "/" + name + "/" + app_name + ".json";
        else if (obj.model.file.endsWith('.acmf') && app_name == "Aspen Custom Modeler")
          params.Key = user_name + "/" + name + "/acm_sinter.json";
        else if (obj.model.file.endsWith('.bkp'))
          params.Key = user_name + "/" + name + "/aspenplus_sinter.json";
        else {
          log(event.body);
          done(new Error(`Inspection sinter config v0.3 failed to identify configuration file type`));
          return;
        }
      }
      else if (obj.filetype == "FOQUS_Session" || obj.Type == "FOQUS_Session") {
        params.Key = user_name + "/" + name + "/session.foqus";
      }
      else {
        log(event.body);
        done(new Error(`Inspection failed to identify configuration file type`));
        return;
      }
    }
    else {
      params.Key = user_name + "/" + name + "/" + key;
    }

    var client = new AWS.S3();
    //var client = s3.createClient(options);
    client.putObject(params, function(err, data) {
      if (err) log(err, err.stack); // an error occurred
      else {
        log("Finished: " + data);
        callback(null, {statusCode:'200', body: "",
          headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/json'}
        });
      }
    });
  }
  else {
          done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
  log('==================================');
  log('Stopping index.handler');
};
