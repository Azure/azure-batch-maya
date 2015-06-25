#-------------------------------------------------------------------------
#
# Batch Apps Maya Plugin
#
# Copyright (c) Microsoft Corporation.  All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the ""Software""), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#--------------------------------------------------------------------------

import os
import webbrowser
import logging

from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
from urllib import unquote

from ui_config import ConfigUI

from batchapps import (
    AzureOAuth,
    Configuration)
from batchapps.exceptions import (
    AuthenticationException,
    InvalidConfigException)

TIMEOUT = 60 # 1 minute

LOG_LEVELS = {
    'debug':10,
    'info':20,
    'warning':30,
    'error':40
    }

class BatchAppsConfig(object):

    def __init__(self, frame, start):

        self.session = start

        self._data_dir = os.path.join(os.path.expanduser('~'), 'BatchAppsData')
        self._ini_file = "batch_apps.ini"

        self._cfg = self._configure_plugin()
        self._log_level = LOG_LEVELS[self._cfg.logging_level().lower()]
        self._creds = None

        self._log = self._configure_logging()
        self._code = None
        
        self.ui = ConfigUI(self, frame)

        self._auth = self.auto_authentication()
        self._update_config_ui()



    @property
    def config(self):
        return self._cfg

    @property
    def credentials(self):
        return self._creds

    @property
    def auth(self):
        return self._auth

    @property
    def path(self):
        return os.path.join(self._data_dir, self._ini_file)

    def _configure_plugin(self):
        cfg = None
        try:
            data_dir = os.path.split(self._data_dir)

            cfg = Configuration(data_path=data_dir[0],
                                name=self._ini_file,
                                datadir=data_dir[1])
            
            cfg.add_jobtype("Maya")
            cfg.current_jobtype("Maya")
            cfg.save_config()
            
        except (InvalidConfigException, IndexError) as exp:
            raise Exception("Error occurred during configuration {0}".format(exp))
            

        if not os.path.isdir(self._data_dir):
            raise EnvironmentError(
                "Data directory not created at '{0}'.\n"
                "Please ensure you have adequate permissions.".format(self._data_dir))

        return cfg

    def _configure_logging(self):
        logger = logging.getLogger('BatchAppsMaya')

        console_format = logging.Formatter(
            "BatchApps: [%(levelname)s] %(message)s")

        file_format = logging.Formatter(
            "%(asctime)-15s [%(levelname)s] %(module)s: %(message)s")

        console_logging = logging.StreamHandler()
        console_logging.setFormatter(console_format)
        logger.addHandler(console_logging)

        logfile = os.path.join(self._data_dir, "batch_apps.log")

        file_logging = logging.FileHandler(logfile)
        file_logging.setFormatter(file_format)
        logger.addHandler(file_logging)

        logger.setLevel(int(self._log_level))
        return logger


    def _update_config_ui(self):
        self.ui.endpoint = self._cfg.endpoint()

        auth_config = self._cfg.aad_config(validate=False)
        self.ui.account = auth_config.get("unattended_account", "")
        self.ui.key = auth_config.get("unattended_key", "")
        self.ui.client = auth_config.get("client_id", "")
        self.ui.tenant = auth_config.get("tenant", "")
        self.ui.redirect = auth_config.get("redirect_uri", "")

        self.ui.logging = self._log_level

        self.ui.set_authenticate(self._auth)

    def set_logging(self, level):

        self._log_level = int(LOG_LEVELS[level])
        self._log.setLevel(self._log_level)

        self._cfg.logging_level(str(level))

    def save_changes(self):
        self._cfg.aad_config(endpoint = self.ui.endpoint, account=self.ui.account, key=self.ui.key,
                             client_id=self.ui.client, tenant=self.ui.tenant,
                             redirect=self.ui.redirect, validate=False)
        self._cfg.save_config()

    def auto_authentication(self):
        try:
            self._log.info("Checking for unattended session...")
            self._creds = AzureOAuth.get_unattended_session(config=self._cfg)
            self._log.info("Found!")
            self.ui.status = "Authenticated via unattended credentials"
            return True

        except (AuthenticationException, InvalidConfigException) as exp:
            self._log.info("Could not get unattended session: {0}".format(exp))

        try:
            self._log.info("Checking for cached session...")
            self._creds = AzureOAuth.get_session(config=self._cfg)
            self._log.info("Found!")
            self.ui.status = "Authenticated via cached credentials"
            return True

        except (AuthenticationException, InvalidConfigException) as exp:
            self._log.info("Could not get cached session: {0}".format(exp))
            self.ui.status = "Unauthenticated"
            return False
      
    def authenticate(self):
        self._cfg = self._configure_plugin()
        self._auth = self.auto_authentication()

        if not self._auth:
            self._auth = self.web_authentication()

        self.ui.set_authenticate(self._auth)
        self.session()

             
    def wait_for_request(self):
        self._code = None

        redirect = self._cfg.aad_config()['redirect_uri'].split(':')
        server_address = (redirect[-2].lstrip('/'), int(redirect[-1]))

        class OAuthRequestHandler(BaseHTTPRequestHandler):

            def log_message(self, format, *args):
                return

            def do_GET(s):
                self.process_response(s)

        web_server = HTTPServer(server_address, OAuthRequestHandler)
        self._log.debug("Created web server listening at: {0}, {1}.".format(
            redirect[-2], int(redirect[-1])))

        web_server.timeout = TIMEOUT
        web_server.handle_request()
        web_server.server_close()
        self._log.debug("Closed server.")

    def open_websession(self):
        try:
            url, state = AzureOAuth.get_authorization_url(config=self._cfg)
            webbrowser.open(url)

            self._log.info("Opened web browser for authentication "
                             "and waiting for response.")

            self.wait_for_request()

        except (AuthenticationException, InvalidConfigException) as exp:
            self._log.error("Unable to open Web UI auth session: "
                              "{0}".format(exp))


    def process_response(self, s):
        self._code = s.path
        if s.path.startswith('/?code'):
            
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()

            s.wfile.write(b"<html><head><title>Authentication Successful</title></head>")
            s.wfile.write(b"<body><p>Authentication successful.</p>")
            s.wfile.write(b"<p>You can now return to Maya where your log in</p>")
            s.wfile.write(b"<p>will be complete in just a moment.</p>")
            s.wfile.write(b"</body></html>")

        else:

            s.send_response(401)
            s.send_header("Content-type", "text/html")
            s.end_headers()

            s.wfile.write(b"<html><head><title>Authentication Failed</title></head>")
            s.wfile.write(b"<body><p>Authentication unsuccessful.</p>")
            s.wfile.write(b"<p>Check the Maya console for details.</p>")
            s.wfile.write(b"</body></html>")

    def decode_error(self, val):
        error_idx = self._code.find(val)
        if error_idx < 0:
            return None

        strt_idx = error_idx + len(val)
        end_idx = self._code.find('&', strt_idx)
        error_val = self._code[strt_idx:end_idx]

        return unquote(error_val)

    def web_authentication(self):

        self.open_websession()

        if not self._code:
            self._log.warning("Log in timed out - please try again.")
            return False

        elif '/?error=' in self._code:
            error = self.decode_error('/?error=')
            details = self.decode_error(
                '&error_description=').replace('+', ' ')

            self._log.error("Authentication failed: {0}".format(error))
            self._log.error(details)
            return False

        else:
            self._log.info(
                "Received valid authentication response from web browser.")
            self._log.info("Now retrieving new authentication token...")

            self._creds = AzureOAuth.get_authorization_token(
                self._code, config=self._cfg)

            self._log.info("Successful! Login complete.")
            return True

