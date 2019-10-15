#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""monitor.py - exposes a Web server while the main loop is running.

See README.md or https://github.com/nicholasadamou/stockflight
for more information.

Copyright (C) Nicholas Adamou 2019
stockflight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import sys
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from threading import Thread

from logs import WARNING

# The host for the monitor Web server.
MONITOR_HOST = "0.0.0.0"

# The port for the monitor Web server.
MONITOR_PORT = 80

# The message returned by the monitor Web server.
MONITOR_MESSAGE = "OK"


class Monitor:
    """A monitor exposing a Web server while the main loop is running."""

    def __init__(self):
        """Creates a Web server on a background thread."""

        try:
            self.server = HTTPServer((MONITOR_HOST, MONITOR_PORT),
                                     self.MonitorHandler)
            self.thread = Thread(target=self.server.serve_forever)
            self.thread.daemon = True
        except KeyboardInterrupt:
            print("%s Ctrl-c keyboard interrupt, exiting." % WARNING)
            sys.exit(0)

    def start(self):
        """Starts the Web server background thread."""

        self.thread.start()

    def stop(self):
        """Stops the Web server and background thread."""

        self.server.shutdown()
        self.server.server_close()

    class MonitorHandler(BaseHTTPRequestHandler):
        """An HTTP request handler that responds with "OK" while running."""

        def _set_headers(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()

        def do_GET(self):
            self._set_headers()
            self.wfile.write(MONITOR_MESSAGE.encode("utf-8"))

        def do_HEAD(self):
            self._set_headers()
