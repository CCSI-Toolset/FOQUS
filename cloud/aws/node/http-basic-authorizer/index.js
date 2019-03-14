/**
 * Lambda Function, Custom HTTP Basic Authorizer.  Uses a DynamoDB table
 * to authenticate/authorize users.
 * @module http-basic-authorizer
 * @author Joshua Boverhof <jrboverhof@lbl.gov>
 * @version 1.0
 * @license See LICENSE.md
 * @see https://github.com/motdotla/node-lambda-template
 */
'use strict';
'use AWS.S3'
'use AWS.DynamoDB'
'use uuid'
const AWS = require('aws-sdk');
const tableName = "TurbineUsers";
exports.handler = function(event, context, callback) {
    console.log('Received event:', JSON.stringify(event, null, 2));
    var headers = event.headers;
    const keys = Object.keys(event.headers);
    for (const key of keys) {
      event.headers[key.toLowerCase()] = event.headers[key];
    }

    if (!headers.authorization ) {
        // WWW-Authenticate: Basic realm="User Visible Realm"
        callback("Unauthorized: No Authorization header");
        return
    }
    var array = headers.authorization.split(' ');
    if (array[0] != "Basic") {
      callback("Unauthorized: Bad Header " + headers.authorization);
      return
    }
    var token = array[1];
    var user = userFromBasicAuthString(token);

    if (!user || !user.name || !user.pass) {
      context.fail("error");
      return;
    }
    console.log("USER: " + user.name + ":" + user.pass);
    /*
    if (user.name === "test" && user.pass === "changeme") {
      //context.succeed(generatePolicy(user.name, 'Allow', event.methodArn));
      callback(null, generateAllow(user.name, event.methodArn));
      return;
    } else {
      context.fail("Unauthorized: " + headers.Authorization);
      return;
    }
    */
    var dynamodb = new AWS.DynamoDB.DocumentClient({apiVersion: '2012-08-10'});
    dynamodb.query({ TableName: tableName,
        KeyConditionExpression: '#N = :user',
        ExpressionAttributeNames: {"#N":"Name"},
        ExpressionAttributeValues: { ":user":user.name}
      },
      function(err,data) {
        if(err) {
          console.log("Error: ", err);
          callback(null, {statusCode:'400', body: JSON.stringify(data), headers: {'Content-Type': 'application/json',}});
        } else {
          //var a = data.Items
          console.log('Data: ', data.Items.length);
          for (var i=0; i<data.Items.length; i++) {
              var item = data.Items[i];
              console.log('item: ', item);
              //obj.push({Name: item.Name, Id: item.Id});
              // Id -- username,
              // Output -- token
              if (item.Name == user.name) {
                //var content = JSON.stringify(obj);
                if (item.Password == user.pass) {
                  console.log("Allow: user=" + user.name);
                  //methodArn="arn:aws:execute-api:us-east-1:754323349409:407osudx4l/dev/GET/session"
                  //policy ARN -> "arn:aws:execute-api:us-east-1:754323349409:407osudx4l/dev/*"
                  var arn_array = event.methodArn.split('/').slice(0,1);
                  arn_array.push('*');
                  var methodArn = arn_array.join( '/' );
                  callback(null, generateAllow(user.name, methodArn));
                  return;
                }
                console.log("Unauthorized: user=" + user.name + ", wrong password");
                context.fail("Unauthorized: " + headers.authorization);
                return;
              }
         }
         console.log("Unauthorized: No such user=" + user.name);
         context.fail("Unauthorized: " + headers.authorization);
        }
  });
}

// Help function to generate an IAM policy
var generatePolicy = function(principalId, effect, resource) {
    // Required output:
    var authResponse = {};
    authResponse.principalId = principalId;
    if (effect && resource) {
        var policyDocument = {};
        policyDocument.Version = '2012-10-17'; // default version
        policyDocument.Statement = [];
        var statementOne = {};
        statementOne.Action = 'execute-api:Invoke'; // default action
        statementOne.Effect = effect;
        statementOne.Resource = resource;
        policyDocument.Statement[0] = statementOne;
        authResponse.policyDocument = policyDocument;
    }
    // Optional output with custom properties of the String, Number or Boolean type.
    //authResponse.context = {
    //    "stringKey": "stringval",
    //    "numberKey": 123,
    //    "booleanKey": true
    //};
    return authResponse;
}

var generateAllow = function(principalId, resource) {
    console.log("Generate Allow Policy(user=" + principalId + "): " + resource);
    return generatePolicy(principalId, 'Allow', resource);
}

var generateDeny = function(principalId, resource) {
    return generatePolicy(principalId, 'Deny', resource);
}

function decodeBase64(str) {
  return new Buffer(str, 'base64').toString();
}



var credentialsRegExp = /^ *(?:[Bb][Aa][Ss][Ii][Cc]) +([A-Za-z0-9\-\._~\+\/]+=*) *$/;

/**
 * RegExp for basic auth user/pass
 *
 * user-pass   = userid ":" password
 * userid      = *<TEXT excluding ":">
 * password    = *TEXT
 * @private
 */

var userPassRegExp = /^([^:]*):(.*)$/;

function userFromBasicAuthString(header) {
  // parse header
  var match = credentialsRegExp.exec(header || '');

  if (!match) {
    if (!header) {
      console.log('no header provided');
      return null;
    }
    // assume the token does not include 'basic '
    match = ['', header];
  }

  // decode user pass
  var userPass = userPassRegExp.exec(decodeBase64(match[1]));

  if (!userPass) {
    return null;
  }

  // return credentials object
  return new Credentials(userPass[1], userPass[2]);
}

/**
 * Decode base64 string.
 * @private
 */

function decodeBase64(str) {
  return new Buffer(str, 'base64').toString();
}

/**
 * Object to represent user credentials.
 * @private
 */

function Credentials(name, pass) {
  this.name = name;
  this.pass = pass;
}
