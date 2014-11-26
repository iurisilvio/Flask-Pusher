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
PUSHER_APP_ID = ''
PUSHER_KEY = ''
PUSHER_SECRET = ''
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


Disclaimer
----------
This project is not affiliated with Pusher or Flask.
