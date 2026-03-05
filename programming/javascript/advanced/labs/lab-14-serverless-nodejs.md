# Lab 14: Serverless Node.js

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build serverless-ready Node.js: Lambda handler structure, cold start optimization, Lambda layers, event sources (API GW/SQS/DynamoDB Streams), middy middleware, and local testing.

---

## Step 1: Lambda Handler Structure

```javascript
// handler.js — basic Lambda handler patterns

// Pattern 1: Simple async handler
exports.hello = async (event, context) => {
  console.log('Event:', JSON.stringify(event));
  console.log('Context:', {
    functionName: context.functionName,
    awsRequestId: context.awsRequestId,
    remainingTimeMs: context.getRemainingTimeInMillis()
  });

  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: 'Hello from Lambda!', timestamp: Date.now() })
  };
};

// Pattern 2: Error handling
exports.withErrorHandling = async (event) => {
  try {
    const result = await processEvent(event);
    return { statusCode: 200, body: JSON.stringify(result) };
  } catch (err) {
    console.error('Error:', err);

    // Never throw unhandled errors from Lambda handlers
    // Return proper HTTP response instead
    return {
      statusCode: err.statusCode ?? 500,
      body: JSON.stringify({
        error: err.message,
        code: err.code ?? 'INTERNAL_ERROR'
      })
    };
  }
};

// Pattern 3: Initialization outside handler (runs once per container)
const AWS = require('aws-sdk');
const db = require('./db'); // Connection established outside handler!

exports.optimized = async (event) => {
  // db is already connected — no cold start penalty on warm invocations
  const result = await db.query('SELECT 1');
  return { statusCode: 200, body: JSON.stringify(result) };
};
```

---

## Step 2: Cold Start Optimization

```javascript
// Minimize cold start time:

// 1. Use lazy initialization for heavy deps
let heavyModule = null;
function getHeavyModule() {
  if (!heavyModule) heavyModule = require('heavy-library');
  return heavyModule;
}

// 2. Keep handler dependencies minimal
// BAD: importing everything
// const AWS = require('aws-sdk');

// GOOD: Import only what you need
const { DynamoDB } = require('@aws-sdk/client-dynamodb');
const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');

// 3. Use the AWS SDK v3 modular imports
const dynamodb = new DynamoDB({ region: process.env.AWS_REGION });

// 4. Reuse connections (DB, Redis) between invocations
let cachedDb = null;
async function getDbConnection() {
  if (!cachedDb) {
    cachedDb = await createDatabaseConnection({
      ssl: { rejectUnauthorized: true }
    });
  }
  return cachedDb;
}

// 5. Use provisioned concurrency for latency-sensitive functions
// Set in AWS console or SAM template:
// ProvisionedConcurrencyConfig:
//   ProvisionedConcurrentExecutions: 5

// 6. Keep Lambda size small — bundle with esbuild/rollup
// esbuild handler.js --bundle --minify --target=node20 --outfile=bundle.js

// Cold start measurement
const INIT_TIME = Date.now();
exports.handler = async (event) => {
  const coldStartMs = Date.now() - INIT_TIME;
  console.log('Cold start lag:', coldStartMs, 'ms');
  return { statusCode: 200, body: JSON.stringify({ coldStart: coldStartMs < 100 }) };
};
```

---

## Step 3: Event Sources

```javascript
// API Gateway event
exports.apiHandler = async (event) => {
  const { httpMethod, path, pathParameters, queryStringParameters, body, headers } = event;

  const userId = pathParameters?.userId;
  const filter = queryStringParameters?.filter;
  const parsedBody = body ? JSON.parse(body) : null;
  const userAgent = headers['User-Agent'];

  console.log(`${httpMethod} ${path}`, { userId, filter });

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'X-Request-Id': event.requestContext?.requestId
    },
    body: JSON.stringify({ userId, data: parsedBody })
  };
};

// SQS event
exports.sqsHandler = async (event) => {
  const failures = [];

  for (const record of event.Records) {
    try {
      const message = JSON.parse(record.body);
      console.log('Processing SQS message:', record.messageId);
      await processMessage(message);
    } catch (err) {
      console.error('Failed to process:', record.messageId, err.message);
      failures.push({ itemIdentifier: record.messageId }); // Partial batch response
    }
  }

  // Partial batch failure response (SQS with reportBatchItemFailures)
  return { batchItemFailures: failures };
};

// DynamoDB Streams event
exports.streamHandler = async (event) => {
  for (const record of event.Records) {
    const { eventName, dynamodb } = record;
    if (!dynamodb) continue;

    const newImage = dynamodb.NewImage
      ? AWS.DynamoDB.Converter.unmarshall(dynamodb.NewImage)
      : null;
    const oldImage = dynamodb.OldImage
      ? AWS.DynamoDB.Converter.unmarshall(dynamodb.OldImage)
      : null;

    console.log(`DynamoDB ${eventName}:`, { new: newImage, old: oldImage });
    await handleStreamRecord(eventName, newImage, oldImage);
  }
};

// S3 event
exports.s3Handler = async (event) => {
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));
    console.log(`S3 ${record.eventName}: s3://${bucket}/${key}`);
    await processS3Object(bucket, key);
  }
};
```

---

## Step 4: Middy Middleware

```javascript
// Middy — onion-model middleware for Lambda
// npm install @middy/core @middy/http-json-body-parser @middy/http-error-handler

const middy = require('@middy/core');
const jsonBodyParser = require('@middy/http-json-body-parser');
const httpErrorHandler = require('@middy/http-error-handler');
const { createError } = require('@middy/util');

// Core handler (clean, no boilerplate)
const coreHandler = async (event) => {
  const { name, email } = event.body; // Already parsed by middleware!
  if (!name) throw createError(400, 'name is required');

  const user = await createUser({ name, email });
  return { statusCode: 201, body: JSON.stringify(user) };
};

// Custom middleware
const authMiddleware = () => ({
  before: async (request) => {
    const token = request.event.headers?.['Authorization']?.replace('Bearer ', '');
    if (!token) throw createError(401, 'Missing auth token');

    const user = await verifyJWT(token);
    request.event.user = user; // Attach to event
  }
});

const loggingMiddleware = () => ({
  before: async (request) => {
    request.event.startTime = Date.now();
    console.log(JSON.stringify({
      type: 'request',
      method: request.event.httpMethod,
      path: request.event.path,
      requestId: request.event.requestContext?.requestId
    }));
  },
  after: async (request) => {
    console.log(JSON.stringify({
      type: 'response',
      status: request.response.statusCode,
      duration: Date.now() - request.event.startTime
    }));
  }
});

// Wrap with middleware
exports.createUser = middy(coreHandler)
  .use(jsonBodyParser())
  .use(authMiddleware())
  .use(loggingMiddleware())
  .use(httpErrorHandler());
```

---

## Step 5: Lambda Layers

```javascript
// Lambda Layers: shared code/dependencies across functions
// Layer structure:
// layer.zip
//   nodejs/
//     node_modules/
//       shared-utils/
//       common-lib/

// Shared utilities layer
// layers/utils/nodejs/index.js
module.exports = {
  logger: require('./logger'),
  db: require('./db'),
  cache: require('./cache')
};

// In your Lambda (layer is mounted at /opt)
const { logger, db, cache } = require('/opt/nodejs/index');

// Alternatively in package.json:
// "dependencies": { "@internal/utils": "file:/opt/nodejs/node_modules/@internal/utils" }

// Build layer:
// mkdir -p layers/utils/nodejs && cd layers/utils/nodejs
// npm install shared-utils common-lib
// cd ../.. && zip -r layer.zip nodejs/
// aws lambda publish-layer-version --layer-name my-utils --zip-file fileb://layer.zip
```

---

## Step 6: Local Testing Simulation

```javascript
// Simulate Lambda invocation locally (no serverless-offline needed)

// local-runner.js
const handler = require('./handler');

// Create mock events
const events = {
  apiGatewayGet: (path, params = {}) => ({
    httpMethod: 'GET',
    path,
    pathParameters: params,
    queryStringParameters: {},
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer test-token' },
    body: null,
    requestContext: { requestId: `local-${Date.now()}` }
  }),

  apiGatewayPost: (path, body) => ({
    httpMethod: 'POST',
    path,
    pathParameters: {},
    queryStringParameters: {},
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    requestContext: { requestId: `local-${Date.now()}` }
  }),

  sqs: (messages) => ({
    Records: messages.map((msg, i) => ({
      messageId: `msg-${i}`,
      body: typeof msg === 'string' ? msg : JSON.stringify(msg),
      attributes: {},
      receiptHandle: `receipt-${i}`
    }))
  })
};

// Mock context
const context = {
  functionName: 'my-function',
  functionVersion: '$LATEST',
  awsRequestId: `local-${Date.now()}`,
  getRemainingTimeInMillis: () => 30000,
  done: () => {},
  fail: () => {},
  succeed: () => {}
};

// Run handler locally
async function invokeLocally(handlerFn, eventType, ...eventArgs) {
  const event = events[eventType](...eventArgs);
  console.log('\n--- INVOKE ---');
  console.log('Event:', JSON.stringify(event, null, 2));
  const response = await handlerFn(event, context);
  console.log('Response:', JSON.stringify(response, null, 2));
  return response;
}

// Test your handler
invokeLocally(handler.hello, 'apiGatewayGet', '/hello');
```

---

## Step 7: SAM/CDK Configuration

```yaml
# template.yaml (AWS SAM)
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: nodejs20.x
    MemorySize: 256
    Timeout: 30
    Environment:
      Variables:
        NODE_ENV: production
        LOG_LEVEL: info

Resources:
  ApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: dist/
      Handler: handler.api
      Layers:
        - !Ref UtilsLayer
      Events:
        HttpApi:
          Type: HttpApi
          Properties:
            Path: /users/{userId}
            Method: GET
      Environment:
        Variables:
          DATABASE_URL: !Sub "{{resolve:secretsmanager:${DBSecret}:SecretString:url}}"
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref UsersTable
      ProvisionedConcurrencyConfig:
        ProvisionedConcurrentExecutions: 2

  UtilsLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      ContentUri: layers/utils/
      CompatibleRuntimes: [nodejs20.x]
      RetentionPolicy: Delete
```

---

## Step 8: Capstone — Lambda Simulation

```javascript
// Lambda handler simulation
const INIT_TIME = Date.now();

const handler = async (event, context) => {
  const isWarm = Date.now() - INIT_TIME > 100;
  const { httpMethod = 'GET', path = '/', body } = event;
  const parsedBody = body ? JSON.parse(body) : null;

  console.log(`${httpMethod} ${path}`, isWarm ? '(warm)' : '(cold start)');

  if (path === '/health') {
    return { statusCode: 200, body: JSON.stringify({ status: 'ok', warm: isWarm }) };
  }

  if (httpMethod === 'POST' && parsedBody?.name) {
    return { statusCode: 201, body: JSON.stringify({ id: Date.now(), ...parsedBody }) };
  }

  return { statusCode: 404, body: JSON.stringify({ error: 'Not found' }) };
};

// Simulate invocations
async function test() {
  const context = { awsRequestId: 'test-123', getRemainingTimeInMillis: () => 29000 };
  
  const r1 = await handler({ httpMethod: 'GET', path: '/health' }, context);
  console.log('Health:', r1.statusCode, JSON.parse(r1.body).status);
  
  const r2 = await handler({ httpMethod: 'POST', path: '/users', body: JSON.stringify({ name: 'Alice' }) }, context);
  console.log('Create:', r2.statusCode, JSON.parse(r2.body).name);
  
  const r3 = await handler({ httpMethod: 'GET', path: '/unknown' }, context);
  console.log('404:', r3.statusCode);
}

test();
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const INIT_TIME = Date.now();
const handler = async (event, context) => {
  const { httpMethod = \"GET\", path = \"/\", body } = event;
  const parsedBody = body ? JSON.parse(body) : null;
  if (path === \"/health\") return { statusCode: 200, body: JSON.stringify({ status: \"ok\" }) };
  if (httpMethod === \"POST\" && parsedBody?.name) return { statusCode: 201, body: JSON.stringify({ id: 1, ...parsedBody }) };
  return { statusCode: 404, body: JSON.stringify({ error: \"Not found\" }) };
};
const ctx = { awsRequestId: \"test\", getRemainingTimeInMillis: () => 29000 };
(async () => {
  const r1 = await handler({ path: \"/health\" }, ctx);
  console.log(\"Health:\", r1.statusCode, JSON.parse(r1.body).status);
  const r2 = await handler({ httpMethod: \"POST\", path: \"/users\", body: JSON.stringify({ name: \"Alice\" }) }, ctx);
  console.log(\"Create:\", r2.statusCode, JSON.parse(r2.body).name);
  const r3 = await handler({ path: \"/unknown\" }, ctx);
  console.log(\"404:\", r3.statusCode);
})();
'"
```

📸 **Verified Output:**
```
Health: 200 ok
Create: 201 Alice
404: 404
```

---

## Summary

| Concept | Key Point | Implementation |
|---------|-----------|----------------|
| Handler structure | `async (event, context) => response` | Return HTTP response object |
| Cold start | Code outside handler runs once | Initialize DB/cache globally |
| Event sources | Different event shapes | API GW, SQS, S3, DynamoDB Streams |
| Middy middleware | Onion model | Auth, validation, error handling |
| Lambda Layers | Shared deps at `/opt/nodejs` | Reduce bundle size |
| Local testing | Mock event/context | Test without deploying |
| Provisioned concurrency | Pre-warm containers | Eliminate cold starts |
| Bundle optimization | esbuild/rollup | Smaller = faster cold start |
