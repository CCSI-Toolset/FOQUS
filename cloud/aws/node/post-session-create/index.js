/**
 * Lambda Function, returns a UUID for a new session resource
 * @module post-session-create
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use uuid'
const uuidv4 = require('uuid/v4');
exports.handler = function(event, context, callback) {
  const done = (err, res) => callback(null, {
      statusCode: err ? '400' : '200',
      body: err ? err.message : JSON.stringify(res),
      headers: {
          'Content-Type': 'application/json',
      },
  });
  if (event.httpMethod == "POST") {
      //var body = JSON.parse(event.body);
      var session_id = uuidv4();
      callback(null, {statusCode:'200', body: JSON.stringify(session_id),
        headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/text'}
      });
  }
  else {
      done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
};
