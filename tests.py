try:
    import unittest2 as unittest
except ImportError:
    import unittest
from decimal import Decimal

import pusher as _pusher
from flask import Flask, json, render_template_string, url_for
from flask_pusher import Pusher, _json_encoder_support, __v1__


pusher_conf = {
    "PUSHER_APP_ID": "1234",
    "PUSHER_KEY": "KEY",
    "PUSHER_SECRET": "SUPERSECRET",
}

SOCKET_ID = "1.42"


class CustomJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(CustomJSONEncoder, self).default(o)


class PusherClientTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(pusher_conf)

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

    def test_json_encoder(self):
        if not _json_encoder_support:
            msg = u"JSON encoder override is not supported on pusher>=1.0,<1.1"
            self.skipTest(msg)

        self.app.json_encoder = CustomJSONEncoder
        pusher = Pusher(self.app)

        with self.app.test_request_context():
            if __v1__:
                enc = pusher.client._json_encoder
            else:
                enc = pusher.client.encoder
        self.assertEqual(CustomJSONEncoder, enc)

    def test_flask_json_patch(self):
        if _json_encoder_support:
            msg = u"Only pusher>=1.0,<1.1 is monkey patched"
            self.skipTest(msg)
        self.assertEqual(json, _pusher.pusher.json)

    def test_configuration(self):
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
        Pusher(self.app)
        with self.app.test_request_context():
            rendered = render_template_string("{{ PUSHER_KEY }}")
            self.assertEqual("KEY", rendered)


class PusherAuthTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.config.update(pusher_conf)
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
                                          "socket_id": SOCKET_ID})
        self.assertEqual(403, response.status_code)

    def test_auth_accepted(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "private-a",
                                          "socket_id": SOCKET_ID})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertIn("auth", data)
        self.assertNotIn("channel_data", data)

    def test_no_channel_data_in_private_channel(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "private-a",
                                          "socket_id": SOCKET_ID})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertIn("auth", data)
        self.assertNotIn("channel_data", data)

    def test_default_channel_data_in_presence_channel(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "presence-a",
                                          "socket_id": SOCKET_ID})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertIn("auth", data)
        channel_data = json.loads(data["channel_data"])
        self.assertEqual({"user_id": SOCKET_ID}, channel_data)

    def test_channel_data_in_presence_channel(self):
        self.pusher.auth(lambda c, s: True)
        self.pusher.channel_data(lambda c, s: {"foo": "bar"})
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "presence-a",
                                          "socket_id": SOCKET_ID})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertIn("auth", data)
        channel_data = json.loads(data["channel_data"])
        self.assertEqual(SOCKET_ID, channel_data["user_id"])
        self.assertIn("bar", channel_data["foo"])

    def test_invalid_channel(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name": "foo",
                                          "socket_id": SOCKET_ID})
        self.assertEqual(404, response.status_code)


class PusherBatchAuthTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.config.update(pusher_conf)
        self.pusher = Pusher(self.app)
        self.client = self.app.test_client()

    def test_one_channel(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name[0]": "private-a",
                                          "socket_id": SOCKET_ID})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertEqual(1, len(data))

        data_a = data.get("private-a")
        self.assertEqual(200, data_a["status"])
        self.assertTrue(data_a["data"])

    def test_more_channels(self):
        self.pusher.auth(lambda c, s: "b" not in c)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name[0]": "private-a",
                                          "channel_name[1]": "private-b",
                                          "channel_name[2]": "presence-c",
                                          "socket_id": SOCKET_ID})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertEqual(3, len(data))

        a = data.get("private-a")
        self.assertEqual(200, a["status"])
        self.assertIn("auth", a["data"])

        b = data.get("private-b")
        self.assertEqual(403, b["status"])

        c = data.get("presence-c")
        self.assertEqual(200, c["status"])
        c_data = c["data"]
        self.assertIn("auth", c_data)
        self.assertIn("channel_data", c_data)

    def test_missing_channel(self):
        self.pusher.auth(lambda c, s: True)
        response = self.client.post("/pusher/auth",
                                    data={"channel_name[1]": "private-b",
                                          "socket_id": SOCKET_ID})
        self.assertEqual(400, response.status_code)


class PusherWebhookTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.config.update(pusher_conf)
        self.pusher = Pusher()
        self.client = self.app.test_client()
        self._called = False

        @self.pusher.webhooks.client
        def c():
            self._called = True

        self.pusher.init_app(self.app)

    def test_no_webhook(self):
        with self.app.test_request_context():
            url = url_for("pusher.presence_event")
        response = self.client.post(url)
        self.assertEqual(404, response.status_code)
        self.assertFalse(self._called)

    def test_without_key_forbidden(self):
        with self.app.test_request_context():
            url = url_for("pusher.client_event")
        response = self.client.post(url)
        self.assertEqual(403, response.status_code)
        self.assertFalse(self._called)

    def test_invalid_key_forbidden(self):
        with self.app.test_request_context():
            url = url_for("pusher.client_event")
        response = self.client.post(url, headers={
            "Content-Type": "application/json",
            "X-Pusher-Key": "meh"
        })
        self.assertEqual(403, response.status_code)
        self.assertFalse(self._called)

    def test_valid_key_forbidden_without_signature(self):
        with self.app.test_request_context():
            url = url_for("pusher.client_event")
        response = self.client.post(url, headers={
            "Content-Type": "application/json",
            "X-Pusher-Key": "KEY"
        })
        self.assertEqual(403, response.status_code)
        self.assertFalse(self._called)

    def test_invalid_signature(self):
        with self.app.test_request_context():
            url = url_for("pusher.client_event")
        response = self.client.post(url, headers={
            "Content-Type": "application/json",
            "X-Pusher-Key": "KEY",
            "X-Pusher-Signature": "x"
        })
        self.assertEqual(403, response.status_code)
        self.assertFalse(self._called)

    def test_valid_signature(self):
        data = '{"a": "b"}'
        with self.app.test_request_context():
            url = url_for("pusher.client_event")
            signature = self.pusher._sign(data)
        response = self.client.post(url, data=data, headers={
            "Content-Type": "application/json",
            "X-Pusher-Key": "KEY",
            "X-Pusher-Signature": signature
        })
        self.assertEqual(200, response.status_code)
        self.assertTrue(self._called)

    def test_hook_all_handlers(self):
        @self.pusher.webhooks.presence
        def h1():
            pass

        @self.pusher.webhooks.channel_existence
        def h2():
            pass


if __name__ == '__main__':
    unittest.main()
