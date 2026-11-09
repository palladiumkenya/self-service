import logging

from flask import current_app, redirect
from flask_appbuilder.const import AUTH_OAUTH
from flask_appbuilder.security.views import AuthOAuthView, expose
from flask_login import current_user
from superset.security import SupersetSecurityManager
from superset_config import CustomUser

logger = logging.getLogger(__name__)


class AuthOIDCView(AuthOAuthView):
    @expose("/login/")
    @expose("/login/<provider>")
    def login(self, provider=None):
        # Skip the provider picker: send users straight to the identity provider.
        return super().login(provider or current_app.config["OAUTH_PROVIDER_NAME"])

    @expose("/oauth-authorized/<provider>")
    def oauth_authorized(self, provider):
        response = super().oauth_authorized(provider)
        landing_page = current_app.config.get("POST_LOGIN_PATH")
        if (
            landing_page
            and current_user.is_authenticated
            and response.location == self.appbuilder.get_url_for_index
        ):
            return redirect(landing_page)
        return response

    @expose("/logout/", methods=["GET", "POST"])
    def logout(self):
        response = super().logout()
        return redirect(current_app.config.get("OIDC_END_SESSION_URI") or response.location)


class OIDCSecurityManager(SupersetSecurityManager):
    authoauthview = AuthOIDCView
    user_model = CustomUser

    @property
    def register_superset_auth_view(self):
        # Superset's own login page would otherwise replace AuthOIDCView.
        return self.auth_type != AUTH_OAUTH

    def get_oauth_user_info(self, provider, resp):
        return dict(self.oauth_remotes[provider].userinfo(token=resp))

    def auth_user_oauth(self, userinfo):
        if self.auth_type != AUTH_OAUTH:
            return None

        email = userinfo.get("email")
        if not email:
            logger.warning("Login rejected: identity provider returned no email")
            return None

        if userinfo.get("UserConfirmed") == "2":
            logger.info("Login rejected: account disabled at identity provider")
            return None

        user = self.find_user(email=email)
        if user is not None and not user.is_active:
            return None
        if user is None:
            user = self._register_oidc_user(userinfo)
        if not user:
            return None

        self.update_user_auth_stat(user)
        return user

    def _register_oidc_user(self, userinfo):
        name_parts = (userinfo.get("name") or userinfo.get("FullName") or "").split()
        if not name_parts:
            logger.warning("Login rejected: account has no name claim")
            return None

        organization_name = userinfo.get("OrganizationName")
        role = self.find_role(organization_name)
        if role is None:
            logger.warning("Login rejected: no role for the account's organization")
            return None

        return self.add_user(
            username=userinfo.get("preferred_username") or userinfo["email"],
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            email=userinfo["email"],
            role=role,
            organization_name=organization_name,
            user_type=userinfo.get("UserType"),
        )

    def add_user(
        self,
        username,
        first_name,
        last_name,
        email,
        role=None,
        password="",
        hashed_password="",
        groups=None,
        organization_name=None,
        user_type=None,
    ):
        user = super().add_user(
            username,
            first_name,
            last_name,
            email,
            role,
            password=password,
            hashed_password=hashed_password,
            groups=groups,
        )
        if user and (organization_name or user_type):
            user.organization_name = organization_name
            user.user_type = user_type
            self.session.merge(user)
            self.session.commit()
        return user
