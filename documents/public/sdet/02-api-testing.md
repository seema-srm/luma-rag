# API Testing Essentials

## API test coverage
Validate status codes, response schemas, important response values, authentication, authorization, and side effects. A successful status alone does not establish correctness. Verify data persistence and error handling where applicable.

## Authentication versus authorization
Authentication establishes identity. Authorization decides whether that identity may perform an action. Test valid credentials, missing credentials, expired credentials, and access to another user's records. Expected error codes depend on the API contract.

## Idempotency
An operation is idempotent when repeating the same operation has the same intended server effect as performing it once. HTTP defines PUT and DELETE as idempotent in their intended semantics; response bodies and status codes can differ across requests. POST is not inherently idempotent, but an API may implement an idempotency-key contract.
