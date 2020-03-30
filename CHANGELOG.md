Changelog
=========
3.0
 * Drop Pusher<1.7 support
 * Drop Flask<0.12 support
 * Support latest Flask (1.1.1) and Pusher (2.1.14)

2.0.2
 * Package README, LICENSE and CHANGELOG

2.0.1
 * Fix README

2.0
 * Remove Python 2.6 and 3.3 support
 * Support `pusher<3`

1.2
 * Support `pusher<2.0`

1.1.1
 * Remove deprecated `flask.ext.*` calls

1.1
 * Support `pusher` 1.2+
 * Support `PUSHER_SSL` configuration

1.0.1
 * Monkey patch `pusher.json` module to use `flask.json`

1.0
 * `pusher>=1.0` support
 * Custom `JSONEncoder` does not work with `pusher==1.0`

0.4.1
 * Fix dependency version: `pusher<1.0`

0.4
 * Batch auth support
 * Configurable url prefix and authentication path

0.3
 * Webhooks support
 * JSONP authentication support with Flask-Jsonpify

0.2
---
 * Authentication support

0.1
---
 * Initial version
 * Flask app binding to pusher client
