Polling
-------
This describes how polling messages from `/communities/`{community}`/channels/`{channel}`/messages` works.

### Requirements For Polling
These are the requirements for long polling to start.

- The `polling` query must not be present or be `true`.
- The `after` query must be sent with a timestamp where no messages are newer than it.

### Rules Of Polling
Unlike normal calls to `/messages`, the `limit` paramater does nothing, and as soon as a new message is present the response is returned with the new message.
