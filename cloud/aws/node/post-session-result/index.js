/**
 * Name:  post-session-result
 * Description: Creates a new key with incremented page number, which signifies
 *   the last page is now closed and returns the last number to the caller.
 * key "s3://{SESSION_BUCKET_NAME}/user_name/session_id/generation_id/page_number"
 * @module post-session-result
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
const log = require("debug")("post-session-result")
const { v4: uuidv4 } = require('uuid');
const AWS = require('aws-sdk');
const tableName = process.env.FOQUS_DYNAMO_TABLE_NAME;
const s3_bucket_name = process.env.SESSION_BUCKET_NAME;
const Set = require("collections/set");

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
    if (event.httpMethod == "POST") {
        var path  = event.path.split('/');
        var gen_id = path.pop(); //ignore this
        if (path.pop() != "result") {
          done(new Error(`Unsupported path "${event.path}"`));
          return;
        }
        const user_name = event.requestContext.authorizer.principalId;
        const session_id = path.pop();
        const s3 = new AWS.S3();
        var prefix = `${user_name}/session/${session_id}/`;
        var next_page_number = 1;

        function handleDone() {
          log("handleDone");
          callback(null, {statusCode:'200', body: next_page_number, headers: {'Content-Type': 'application/json',}});
        };
        function handleError() {
          log("handleDone");
          callback(null, {statusCode:'500', body: `{"session":"${session_id}", "Message":"Error processessing documents"}`,
            headers: {'Content-Type': 'application/json',}});
        };
        /*
         *  putS3JobPage: Grabs all finished jobs from S3.  Keys contain
         *     timestamps (ms since epoch) which are used to sort.  Page
         *     key created with largest timestamp of all jobs contained
         *     in array.  New page number is incremented from number of
         *     keys starting with "page" prefix.  All jobs that are newer
         *     than timestamp of newest page are put in the current page.
         *     NOTE: Currently this algorithm will fail if jobs have same
         *        timestamp in key and the last page to return contained
         *        a subset of the jobs.  Very unlikely to occur but..
         */
        function putS3JobPage(response) {
            var promises = [];
            var job_ms = 0;
            var max_job_ms = 0;
            var page_ms = 0;
            var job_id = "";
            const job_paged_set = new Set();
            log("getS3Objects: " + JSON.stringify(response));

            if (response.IsTruncated) {
                //params.ContinuationToken = response.NextContinuationToken;
                log("s3 list keys is truncated");
                throw new Error("s3 list keys is truncated breaking results algorithm")
            }

            for (var index = 0; index < response.Contents.length; ++index) {
              var key = response.Contents[index].Key;
              if (key.includes('/page/')) {
                //byron/session/21c0971a-b25b-40ac-ba07-bd1b487a2d6b/page/milliseconds/1588077775166.json
                if (key.includes('/page/number/')) {
                  //page_ms = Math.max(page_ms, parseInt(key.split('/')[5]));
                  //log(`key: ${key}`);
                  //log(`page_ms: ${page_ms} ${parseInt(key.split('/')[5])}`)
                  next_page_number +=1
                }
                continue;
              }
              if (key.includes('/paged/')) {
                if (key.includes('/paged/job/')) {
                  job_id = key.split('/')[5];
                  log(`paged job: ${job_id}`);
                  job_paged_set.add(job_id);
                }
                continue;
              }
            }
            for (var index = 0; index < response.Contents.length; ++index) {
              var key = response.Contents[index].Key;
              log("KEY: " + key);
              var params = {
                Bucket: s3_bucket_name,
                Key: key,
              };
              // byron/session/{session_id}/finished/{milliseconds}/success/{job_id}.json
              if (key.includes('/finished/')) {
                //job_ms = parseInt(key.split('/')[4]);
                //log(`job_ms ${job_ms}`);
                //if (job_ms > page_ms) {
                  //log(`promise: get ${key}`)
                  //max_job_ms = Math.max(max_job_ms, job_ms);

                job_id = key.split('/')[6].split('.')[0];
                if (!job_paged_set.has(job_id)) {
                  log(`page job: ${job_id}`)
                  let promise = s3.getObject(params).promise();
                  promises.push(promise);
                } else {
                  log(`job already paged: ${job_id}`)
                }
              }
            }
            // Put All S3 Objects in Page
            var page = [];
            Promise.all(promises).then(function(values) {
              for (var i=0 ; i < values.length; i++ ) {
                var data = values[i];
                var obj = JSON.parse(data.Body.toString('ascii'));
                page.push(obj);
                // ledger of paged jobs
                var key = `${user_name}/session/${session_id}/paged/job/${obj.Id}`;
                var requestx = s3.putObject({Bucket: s3_bucket_name, Key: key, Body: JSON.stringify(obj)});
                requestx.promise();
              }
              log(`pagelen: ${page.length}`);
              if (page.length == 0) {
                // There were no new Finished jobs, return latest result page
                // number
                next_page_number = next_page_number - 1;
                handleDone();
                return;
              }
              //var key = `${user_name}/session/${session_id}/page/milliseconds/${max_job_ms}.json`;
              var content = JSON.stringify(page);
              var request = s3.putObject({Bucket: s3_bucket_name, Key: key, Body: content});
              var key = `${user_name}/session/${session_id}/page/number/${next_page_number}.json`;
              var request2 = s3.putObject({Bucket: s3_bucket_name, Key: key, Body: content});

              request2.promise();
              request.promise().then(handleDone).catch(handleError);
            });
        };
        var request = s3.listObjectsV2({Bucket: s3_bucket_name, MaxKeys: 1000,
                        Prefix: prefix, StartAfter: prefix});
        request.promise().then(putS3JobPage);
    }
    else {
        done(new Error(`Unsupported method "${event.httpMethod}"`));
    }
};
