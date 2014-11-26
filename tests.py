import unittest
from decimal import Decimal

from flask import Flask, json
import pusher as _pusher
from flask.ext.pusher import Pusher

# pusher client global app_id
_pusher.app_id = "1234"


class CustomJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(CustomJSONEncoder, self).default(o)


class PusherClientTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)

    def test_default_config(self):
        # fallback to Pusher globals still works
        pusher = Pusher(self.app)
        with self.app.app_context():
            self.assertIsNotNone(pusher.client)

    def test_set_app_id(self):
        app_id = "4321"
        self.app.config["PUSHER_APP_ID"] = app_id
        pusher = Pusher(self.app)
        with self.app.app_context():
            self.assertIsNotNone(pusher.client)
            self.assertEqual(app_id, pusher.client.app_id)

    def test_json_encoder(self):
        self.app.json_encoder = CustomJSONEncoder
        pusher = Pusher(self.app)

        with self.app.app_context():
            self.assertEqual(CustomJSONEncoder, pusher.client.encoder)

    def test_configuration(self):
        self.app.config["PUSHER_KEY"] = "KEY"
        self.app.config["PUSHER_SECRET"] = "SUPERSECRET"
        self.app.config["PUSHER_HOST"] = "example.com"
        self.app.config["PUSHER_PORT"] = 8080
        pusher = Pusher(self.app)
        with self.app.app_context():
            self.assertIsNotNone(pusher.client)
            self.assertEqual("KEY", pusher.client.key)
            self.assertEqual("SUPERSECRET", pusher.client.secret)
            self.assertEqual("example.com", pusher.client.host)
            self.assertEqual(8080, pusher.client.port)

if __name__ == '__main__':
    unittest.main()
