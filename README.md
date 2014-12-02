Flask-Pusher
============

Flask extension for Pusher. It is a thin wrapper around the official client,
binding Flask app to Pusher client.

Installation
------------

Install `Flask-Pusher` module from PyPI.

```
pip install Flask-Pusher
```

Configuration
-------------

The basic configuration for Pusher is `app_id`, `key` and `secret`. These values are available in Pusher web interface.

```python
PUSHER_APP_ID = 'your-pusher-app-id'
PUSHER_KEY = 'your-pusher-key'
PUSHER_SECRET = 'your-pusher-secret'
```

You can connect to a custom host/port, with these configurations:

```python
PUSHER_HOST = 'api.pusherapp.com'
PUSHER_PORT = '80'
```

The extension auto configure the Pusher encoder to use the `app.json_encoder`.

Usage
-----

This extension simplify Pusher configuration and bind the client to your app.

```python
from flask import Flask
from flask.ext.pusher import Pusher

app = Flask(__name__)
pusher = Pusher(app)
```

The extension gives you two ways to access the pusher client:

```python
# you can just get the client from current_app
client = current_app.extensions["pusher"]

# or you can get it from the extension
client = pusher.client
```

In both cases, it is a reference to the pusher client.

```
client[channel_name].trigger('event', {
    'message': msg,
})
```

Check the docs for the Pusher python client here: http://pusher.com/docs/server_api_guide#/lang=python

Pusher authentication
---------------------

Pusher has authenticated private and presence channels. `Flask-Pusher` create
the `/pusher/auth` route to handle it. To support these authenticated routes,
just decorate a function with `@pusher.auth`.

This function must return `True` for authorized and `False` for unauthorized
users. It happens in the request context, so you have all `Flask` features,
including for exemple the `Flask-Login` current user.

```python
from flask.ext.login import current_user

@pusher.auth
def pusher_auth(channel_name, socket_id):
    if 'foo' in channel_name:
        # refuse foo channels
        return False
    # authorize only authenticated users
    return current_user.is_authenticated()
```

Read more about user authentication here: http://pusher.com/docs/authenticating_users

Pusher channel data
-------------------

Presence channels require `channel_data`. `Flask-Pusher` send by default the
`user_id` with the `socket_id`, because it is a required field.

The `@pusher.channel_data` gives you a way to set other values. If a `user_id`
key is returned, it overrides the default `user_id`.

```python
@pusher.channel_data
def pusher_channel_data(channel_name, socket_id):
    return {
        "name": current_user.name
    }
```

Disclaimer
----------
This project is not affiliated with Pusher or Flask.
