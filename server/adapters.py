from oauth2.web import ResourceOwnerGrantSiteAdapter
from oauth2.error import UserNotAuthenticated
from passlib.hash import pbkdf2_sha256
from models import AuthUser, AuthClient
from constants import USER_STATUS


class AuthSiteAdapter(ResourceOwnerGrantSiteAdapter):
    def authenticate(self, request, environ, scopes, client):
        username = request.handler.get_argument('username', None)
        password = request.handler.get_argument('password', '')
        auth_user = AuthUser.get(oauth_username=username, get_first=True)
        auth_client = AuthClient.get(oauth_id=client.identifier, get_first=True)
        if auth_user and auth_user.status == USER_STATUS.ACTIVE and \
                pbkdf2_sha256.verify(password, auth_user.oauth_password) and \
                auth_user.client_id == auth_client.id:
            return auth_user.meta_info, auth_user.oauth_username
        raise UserNotAuthenticated
