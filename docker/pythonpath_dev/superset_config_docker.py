import json
import os

from flask_appbuilder.const import AUTH_DB, AUTH_OAUTH

from customSecurity import OIDCSecurityManager

# AUTHENTICATION
AUTH_MODES = {"db": AUTH_DB, "oauth": AUTH_OAUTH}
AUTH_TYPE = AUTH_MODES[os.environ.get("SUPERSET_AUTH_MODE", "oauth")]
AUTH_USER_REGISTRATION = False
AUTH_USER_REGISTRATION_ROLE = "Gamma"
CUSTOM_SECURITY_MANAGER = OIDCSecurityManager

if AUTH_TYPE == AUTH_OAUTH:
    OAUTH_PROVIDER_NAME = "kenyahmis"
    POST_LOGIN_PATH = "/superset/dashboard/1822/"

    with open(
        os.path.join(os.path.dirname(__file__), "client_secret.json"), encoding="utf-8"
    ) as client_secret_file:
        _oidc_client = json.load(client_secret_file)["web"]

    OIDC_END_SESSION_URI = _oidc_client.get("end_session_uri")
    OAUTH_PROVIDERS = [
        {
            "name": OAUTH_PROVIDER_NAME,
            "icon": "fa-key",
            "token_key": "access_token",
            "remote_app": {
                "client_id": _oidc_client["client_id"],
                "client_secret": _oidc_client["client_secret"],
                "server_metadata_url": (
                    _oidc_client["issuer"].rstrip("/")
                    + "/.well-known/openid-configuration"
                ),
                "client_kwargs": {
                    "scope": "openid email",
                    "token_endpoint_auth_method": "client_secret_post",
                },
            },
        }
    ]

FAB_API_SWAGGER_UI = False

ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {"x_for": 1, "x_proto": 1, "x_host": 1, "x_port": 0, "x_prefix": 1}

PREVIOUS_SECRET_KEY = os.environ.get("PREVIOUS_SECRET_KEY", "")
SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

# EMAIL CONFIGURATION
ALERT_REPORTS = True
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False
EMAIL_NOTIFICATIONS = True  # all the emails are sent using dryrun
SMTP_HOST = "smtp.mailgun.org"
SMTP_STARTTLS = True
SMTP_SSL = False
SMTP_USER = "datawarehouse-adhoc@mg.kenyahmis.org"
SMTP_PORT = 587
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
SMTP_MAIL_FROM = "selfservice-dwh@mg.kenyahmis.org"
# If True creates a default SSL context with ssl.Purpose.CLIENT_AUTH using the
# default system root CA certificates.
SMTP_SSL_SERVER_AUTH = False
ENABLE_CHUNK_ENCODING = False

# reports
WEBDRIVER_TYPE = "chrome"
WEBDRIVER_OPTION_ARGS = [
    "--force-device-scale-factor=2.0",
    "--high-dpi-support=2.0",
    "--headless",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-extensions",
]

SUPERSET_WEBSERVER_TIMEOUT = 300
