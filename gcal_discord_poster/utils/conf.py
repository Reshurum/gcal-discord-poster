# MIT License
#
# Copyright (c) 2019 Walter Kuppens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Contains helper functions for retrieving configuration."""

import json
import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


CONFIG_DIR = "~/.config/gcal-discord-poster"
CONFIG_FILE_NAME = "config.json"

# Google API scopes required for the operation of this tool.
SCOPES = {
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
}

LOG = logging.getLogger("gcal-discord-poster")


def get_new_google_credentials(
        config: dict, client_id_path: str, save=True) -> Credentials:
    """Obtains new Google access credentials via interactive OAuth2 flow."""

    flow = InstalledAppFlow.from_client_secrets_file(
        client_id_path,
        scopes=SCOPES)
    credentials = flow.run_local_server(
        host='localhost',
        port=8098,
        authorization_prompt_message='Please visit this URL: {url}',
        success_message='The auth flow is complete; you may close this window.',
        open_browser=True)

    if save:
        stash_google_credentials(config, credentials)
        save_config(config)

    return credentials


def get_saved_google_credentials(config: dict) -> Credentials:
    """Returns saved Google access credentials stored in the config."""

    credentials_dict = config.get("oauth", {}).get("google", {})
    if (
            not credentials_dict
            or "refresh_token" not in credentials_dict
            or "client_id" not in credentials_dict
            or "client_secret" not in credentials_dict
    ):
        return None

    credentials = Credentials(**credentials_dict)
    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            return None

    return credentials

def stash_google_credentials(config: dict, credentials: Credentials) -> dict:
    """Stash Google OAuth2 credentials in a config dict."""

    if "oauth" not in config:
        config["oauth"] = {}

    config["oauth"]["google"] = {
        "refresh_token": credentials.refresh_token,
        "token": credentials.token,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "token_uri": credentials.token_uri,
    }

    return config


def setup_config_dir():
    """Makes sure the config directory exists."""

    real_config_dir = os.path.expanduser(CONFIG_DIR)

    if not os.path.exists(real_config_dir):
        os.makedirs(real_config_dir)
    elif not os.path.isdir(real_config_dir):
        msg = "Unable to setup config dir at '%s'"
        LOG.error(msg, CONFIG_DIR)
        raise RuntimeError(msg % CONFIG_DIR)


def get_config_path() -> str:
    """Builds a filepath to the config directory."""

    return os.path.join(os.path.expanduser(CONFIG_DIR), CONFIG_FILE_NAME)


def get_config() -> dict:
    """Reads the autogenerated config file from the filesystem.

    If the parent config directory doesn't exist, one will be created. The
    config file itself is simply a json file that contains auth information
    and user preferences.
    """

    config_path = get_config_path()

    if os.path.isdir(config_path):
        msg = "Config path at '%s' is a directory."
        LOG.error(msg, config_path)
        raise RuntimeError(msg % config_path)

    if os.path.isfile(config_path):
        with open(config_path, "r") as file:
            config = json.load(file)
    else:
        config = {}

    return config


def save_config(config: dict):
    """Saves a config to the filesystem.

    If the parent config directory doesn't exist, one will be created. The
    existing config file, if present, will be completely overwritten.
    """

    config_path = get_config_path()

    if os.path.isdir(config_path):
        msg = "Config path at '%s' is a directory."
        LOG.error(msg, config_path)
        raise RuntimeError(msg % config_path)

    setup_config_dir()

    with open(config_path, "w") as file:
        json.dump(config, file, indent=4, sort_keys=True)