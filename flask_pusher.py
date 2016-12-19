import hashlib
import hmac
import inspect

from flask import Blueprint, current_app, request, abort, json
try:
    from flask_jsonpify import jsonify
except ImportError:
    from flask import jsonify

import pusher as _pusher

try:
    from pusher.signature import sign, verify

    argspec = inspect.getargspec(_pusher.Pusher.__init__)
    if "json_encoder" not in argspec.args:
        # monkey patch pusher json module because they don't have
        # any option to define my own json encoder
        _pusher.pusher.json = json
except ImportError:
    _pusher.json = json

    def sign(key, message):
        return hmac.new(key, message, hashlib.sha256).hexdigest()

    def verify(key, message, signature):
        return sign(key, message) == signature


class _Pusher(_pusher.Pusher):
    """
    Pusher client wrapper to get attributes from `_pusher_client`
    if the attribute does not exist.

    Provide backward compatibility to `pusher>=1.6`.
    """
    def __getattr__(self, attr):
        if hasattr(self, "_pusher_client"):
            client = self._pusher_client
            return getattr(client, attr)
        else:
            # call super to raise the original exception
            return getattr(super(_Pusher, self), attr)


class Pusher(object):

    def __init__(self, app=None, url_prefix="/pusher"):
        self.app = app
        self._auth_handler = None
        self._channel_data_handler = None
        self._blueprint = Blueprint('pusher', __name__, url_prefix=url_prefix)
        self.webhooks = Webhooks(self)

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        # if config not defined, Pusher will fallback to default config
        app.config.setdefault("PUSHER_APP_ID", '')
        app.config.setdefault("PUSHER_KEY", '')
        app.config.setdefault("PUSHER_SECRET", '')
        app.config.setdefault("PUSHER_HOST", '')
        app.config.setdefault("PUSHER_PORT", '')
        app.config.setdefault("PUSHER_AUTH", '/auth')

        pusher_kwargs = dict(
            app_id=app.config["PUSHER_APP_ID"],
            key=app.config["PUSHER_KEY"],
            secret=app.config["PUSHER_SECRET"],
            host=app.config["PUSHER_HOST"],
            port=app.config["PUSHER_PORT"],
        )

        ssl = app.config.get('PUSHER_SSL')
        if ssl is not None:
            pusher_kwargs["ssl"] = ssl

        timeout = app.config.get('PUSHER_TIMEOUT')
        if timeout is not None:
            pusher_kwargs["timeout"] = timeout

        cluster = app.config.get('PUSHER_CLUSTER')
        if cluster is not None:
            pusher_kwargs["cluster"] = cluster

        backend = app.config.get('PUSHER_BACKEND')
        if backend is not None:
            pusher_kwargs["backend"] = backend

        notification_host = app.config.get('PUSHER_NOTIFICATION_HOST')
        if notification_host is not None:
            pusher_kwargs["notification_host"] = notification_host

        notification_ssl = app.config.get('PUSHER_NOTIFICATION_SSL')
        if notification_ssl is not None:
            pusher_kwargs["notification_ssl"] = notification_ssl

        argspec = inspect.getargspec(_pusher.Pusher.__init__)
        expected_args = set(argspec.args)
        ignored_args = []
        for key, value in pusher_kwargs.items():
            if key not in expected_args:
                ignored_args.append(key)
                del pusher_kwargs[key]

        if ignored_args:
            message = u"Flask-Pusher ignored some incompatible args: %s"
            app.logger.warning(message % ignored_args)

        if "json_encoder" in argspec.args:
            pusher_kwargs.update({
                "json_encoder": getattr(app, "json_encoder", None),
                "json_decoder": getattr(app, "json_decoder", None),
            })
        else:
            pusher_kwargs["encoder"] = getattr(app, "json_encoder", None)

        backend_options = app.config.get('PUSHER_BACKEND_OPTIONS')
        if backend_options is not None:
            if argspec.keywords == "backend_options":
                pusher_kwargs.update(backend_options)
            else:
                message = u"Flask-Pusher ignored incompatible backend_options."
                app.logger.warning(message)

        client = _Pusher(**pusher_kwargs)

        self._make_blueprint(app.config["PUSHER_AUTH"])
        app.register_blueprint(self._blueprint)

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

    def _make_blueprint(self, auth_path):
        bp = self._blueprint

        @bp.route(auth_path, methods=["POST"])
        def auth():
            if not self._auth_handler:
                abort(403)

            socket_id = request.form["socket_id"]
            channel_name = request.form.get("channel_name")
            if channel_name:
                response = self._auth_simple(socket_id, channel_name)
                if not response:
                    abort(403)
            else:
                response = self._auth_buffered(socket_id)
            return jsonify(response)

        @bp.app_context_processor
        def pusher_data():
            return {
                "PUSHER_KEY": self.client.key
            }

    def _sign(self, message):
        return sign(self.client.secret, message)

    def _verify(self, message, signature):
        if not signature:
            return False
        return verify(self.client.secret, message, signature)

    def _auth_simple(self, socket_id, channel_name):
        if not self._auth_handler(channel_name, socket_id):
            return None
        return self._auth_key(socket_id, channel_name)

    def _auth_buffered(self, socket_id):
        response = {}
        while True:
            n = len(response)
            channel_name = request.form.get("channel_name[%d]" % n)
            if not channel_name:
                if n == 0:
                    # it is not a buffered request
                    abort(400)
                break
            r = {}
            auth = self._auth_simple(socket_id, channel_name)
            if auth:
                r.update(status=200, data=auth)
            else:
                r.update(status=403)
            response[channel_name] = r
        return response

    def _auth_key(self, socket_id, channel_name):
        if channel_name.startswith("presence-"):
            channel_data = {"user_id": socket_id}
            if self._channel_data_handler:
                d = self._channel_data_handler(channel_name, socket_id)
                channel_data.update(d)
            auth_args = [socket_id, channel_data]
        elif channel_name.startswith("private-"):
            auth_args = [socket_id]
        else:
            # must never happen, this request is not from pusher
            abort(404)

        try:
            channel = self.client[channel_name]
        except TypeError:
            # pusher>=1.0
            auth = self.client.authenticate(channel_name, *auth_args)
        else:
            # pusher<1.0
            auth = channel.authenticate(*auth_args)

        return auth


class Webhooks(object):

    CHANNEL_EXISTENCE_EVENT = "channel_existence"
    PRESENCE_EVENT = "presence"
    CLIENT_EVENT = "client"

    def __init__(self, pusher):
        self.pusher = pusher
        self._handlers = {}
        self._register(self.CHANNEL_EXISTENCE_EVENT)
        self._register(self.PRESENCE_EVENT)
        self._register(self.CLIENT_EVENT)

    def channel_existence(self, func):
        self._handlers[self.CHANNEL_EXISTENCE_EVENT] = func
        return func

    def presence(self, func):
        self._handlers[self.PRESENCE_EVENT] = func
        return func

    def client(self, func):
        self._handlers[self.CLIENT_EVENT] = func
        return func

    def _register(self, event):
        def route():
            func = self._handlers.get(event)
            if not func:
                abort(404)
            self._validate()
            func()
            return "OK", 200

        rule = "/events/%s" % event
        name = "%s_event" % event
        self.pusher._blueprint.add_url_rule(rule, name, route,
                                            methods=["POST"])

    def _validate(self):
        pusher_key = request.headers.get("X-Pusher-Key")
        if pusher_key != self.pusher.client.key:
            # invalid pusher key
            abort(403)

        webhook_signature = request.headers.get("X-Pusher-Signature")
        if not self.pusher._verify(request.data.decode(), webhook_signature):
            # invalid signature
            abort(403)
