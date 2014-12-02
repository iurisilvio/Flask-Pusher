from flask import Blueprint, current_app, request, jsonify, abort

import pusher as _pusher


class Pusher(object):

    def __init__(self, app=None):
        self.app = app
        self._auth_handler = None
        self._channel_data_handler = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        # if config not defined, Pusher will fallback to default config
        app.config.setdefault("PUSHER_APP_ID", '')
        app.config.setdefault("PUSHER_KEY", '')
        app.config.setdefault("PUSHER_SECRET", '')
        app.config.setdefault("PUSHER_HOST", '')
        app.config.setdefault("PUSHER_PORT", '')

        client = _pusher.Pusher(
            app_id=app.config["PUSHER_APP_ID"],
            key=app.config["PUSHER_KEY"],
            secret=app.config["PUSHER_SECRET"],
            host=app.config["PUSHER_HOST"],
            port=app.config["PUSHER_PORT"],
            encoder=app.json_encoder)

        bp = self._make_blueprint()
        app.register_blueprint(bp)

        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["pusher"] = client

    @property
    def client(self):
        return current_app.extensions.get("pusher")

    def auth(self, handler):
        self._auth_handler = handler
        return handler

    def channel_data(self, handler):
        self._channel_data_handler = handler
        return handler

    def _make_blueprint(self):
        bp = Blueprint('pusher', __name__)

        @bp.route("/pusher/auth", methods=["POST"])
        def auth():
            if not self._auth_handler:
                abort(403)

            channel_name = request.form["channel_name"]
            socket_id = request.form["socket_id"]

            if not self._auth_handler(channel_name, socket_id):
                abort(403)

            channel = self.client[channel_name]
            if channel_name.startswith("presence-"):
                channel_data = {"user_id": socket_id}
                if self._channel_data_handler:
                    d = self._channel_data_handler(channel_name, socket_id)
                    channel_data.update(d)
                auth = channel.authenticate(socket_id, channel_data)
            elif channel_name.startswith("private-"):
                auth = channel.authenticate(socket_id)
            else:
                # must never happen, this request is not from pusher
                abort(404)
            return jsonify(auth)

        @bp.app_context_processor
        def pusher_data():
            return {
                "PUSHER_KEY": self.client.key
            }

        return bp
