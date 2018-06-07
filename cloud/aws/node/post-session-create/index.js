'use strict';
'use uuid'
// https://github.com/motdotla/node-lambda-template
// NOTE:  CORS For Integrated Lambda Proxy Must be done in Lambda functions
//  because "Integration Response" is disabled, CORS settings will not work!
//  Follow the link:
//     https://stackoverflow.com/questions/40149788/aws-api-gateway-cors-ok-for-options-fail-for-post
//
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
      callback(null, {statusCode:'200', body: session_id,
        headers: {'Access-Control-Allow-Origin': '*','Content-Type': 'application/text'}
      });
  }
  else {
      done(new Error(`Unsupported method "${event.httpMethod}"`));
  }
};
