# FOQUS AWS Cloud

## Backend: Node.js Lambda Functions (node v6.1.0)

## API Front end
### Session Resource
#### GET session
-- returns JSON array of all sessions
#### POST session
-- return session UUID
#### GET session/{id}
-- returns JSON array of all "metadata" for jobs in session
#### POST session/{id}/start
-- sends all jobs in session to submit queue
#### POST session/{id}
-- sends all jobs in session to submit queue
