from auth_stores import AccessTokenStore
from base_handler import BaseHandler

from oauth2.error import AccessTokenNotFound


class AuthValidationHandler(BaseHandler):
    def get(self):
        access_token = self.get_argument('access_token')
        if access_token:
            try:
                token_data = AccessTokenStore.fetch_data_for_access_token(access_token)
                response_str = self.prepare_response(status='valid access token', **token_data)
                self.write(response_str)
            except AccessTokenNotFound:
                self.send_error(status_code=401, error_description='Invalid or Expired Access Token')
