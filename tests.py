try:
    import unittest2 as unittest
except ImportError:
    import unittest
from decimal import Decimal

from flask import Flask, json, render_template_string, url_for
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
        with self.app.test_request_context():
            self.assertIsNotNone(pusher.client)

    def test_lazy_init_app(self):
        pusher = Pusher()
        pusher.init_app(self.app)
        with self.app.test_request_context():
            self.assertIsNotNone(pusher.client)

    def test_create_extensions_map(self):
        del self.app.extensions
        pusher = Pusher(self.app)
        with self.app.test_request_context():
            self.assertIsNotNone(pusher.client)

    def test_set_app_id(self):
        app_id = "4321"
        self.app.config["PUSHER_APP_ID"] = app_id
        pusher = Pusher(self.app)
        with self.app.test_request_context():
            self.assertIsNotNone(pusher.client)
            self.assertEqual(app_id, pusher.client.app_id)

    def test_json_encoder(self):
        self.app.json_encoder = CustomJSONEncoder
        pusher = Pusher(self.app)

        with self.app.test_request_context():
            self.assertEqual(CustomJSONEncoder, pusher.client.encoder)

    def test_configuration(self):
        self.app.config["PUSHER_KEY"] = "KEY"
        self.app.config["PUSHER_SECRET"] = "SUPERSECRET"
        self.app.config["PUSHER_HOST"] = "example.com"
        self.app.config["PUSHER_PORT"] = 8080
        pusher = Pusher(self.app)
        with self.app.test_request_context():
            self.assertIsNotNone(pusher.client)
            self.assertEqual("KEY", pusher.client.key)
            self.assertEqual("SUPERSECRET", pusher.client.secret)
            self.assertEqual("example.com", pusher.client.host)
            self.assertEqual(8080, pusher.client.port)

    def test_pusher_key_in_template(self):
        self.app.config["PUSHER_KEY"] = "KEY"
        Pusher(self.app)
        with self.app.test_request_context():
            rendered = render_template_string("{{ PUSHER_KEY }}")
            self.assertEqual("KEY", rendered)


class PusherAuthTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.config["PUSHER_KEY"] = "KEY"
        self.app.config["PUSHER_SECRET"] = "SUPERSECRET"
        self.pusher = Pusher(self.app)
        self.client = self.app.test_client()

    def test_url_for(self):
        with self.app.test_request_context():
            url = url_for("pusher.auth")
        self.assertEqual("/pusher/auth", url)

    def test_forbidden_withuot_auth_handler(self):
        response = self.client.post("/pusher/auth")
        self.assertEqual(403, response.status_code)

    def test_auth_refused(self):
        self.pusher.auth(lambda c, s: False)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "private-a",
                                          "socket_id": "1"})
        self.assertEqual(403, response.status_code)

    def test_auth_accepted(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "private-a",
                                          "socket_id": "1"})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertIn("auth", data)
        self.assertNotIn("channel_data", data)

    def test_no_channel_data_in_private_channel(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "private-a",
                                          "socket_id": "1"})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertIn("auth", data)
        self.assertNotIn("channel_data", data)

    def test_default_channel_data_in_presence_channel(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "presence-a",
                                          "socket_id": "1"})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertIn("auth", data)
        channel_data = json.loads(data["channel_data"])
        self.assertEqual({"user_id": "1"}, channel_data)

    def test_channel_data_in_presence_channel(self):
        self.pusher.auth(lambda c, s: True)
        self.pusher.channel_data(lambda c, s: {"foo": "bar"})
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "presence-a",
                                          "socket_id": "1"})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertIn("auth", data)
        channel_data = json.loads(data["channel_data"])
        self.assertEqual("1", channel_data["user_id"])
        self.assertIn("bar", channel_data["foo"])

    def test_invalid_channel(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "foo",
                                          "socket_id": "1"})
        self.assertEqual(404, response.status_code)


if __name__ == '__main__':
    unittest.main()
