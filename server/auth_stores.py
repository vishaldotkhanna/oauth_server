from oauth2.store import ClientStore
from oauth2.datatype import Client, AccessToken
from oauth2.store.redisdb import TokenStore
from oauth2.error import ClientNotFoundError, AccessTokenNotFound
from models import AuthUser, AuthClient, redis
from ast import literal_eval
from time import time


ACCESS_TOKEN_REDIS_TTL = 900
REFRESH_TOKEN_REDIS_TTL = 1800

fields_to_remove_from_response = ['expires_at', 'refresh_expires_at']


class AuthUserStore(ClientStore):
    def fetch_by_client_id(self, client_id):
        auth_client = AuthClient.get(oauth_id=client_id, get_first=True)
        if auth_client:
            return Client(identifier=auth_client.oauth_id,
                          secret=auth_client.oauth_secret)
        raise ClientNotFoundError


class AccessTokenStore(TokenStore):
    token_key_prefix = 'auth'

    def save_token(self, access_token):
        if not access_token.refresh_token:  # Reset refresh_token expiry when saving from RefreshTokenGrant flow.
            self.add_old_refresh_to_access_token(access_token)
        self.delete_old_tokens_for_user(access_token.user_id)
        self.save_keys_for_token(access_token)

    def fetch_existing_token_of_user(self, client_id, grant_type, user_id):
        token_data = self.fetch_data_for_key(user_id)
        access_token = token_data.get('token')
        existing_token = self.fetch_data_for_access_token(access_token,
                                                          return_type='access_token',
                                                          user_data_dict=token_data)
        self.reset_existing_token_expiry(existing_token)
        return existing_token

    def fetch_by_refresh_token(self, refresh_token):
        token_data = self.fetch_data_for_key(refresh_token, key_type='refresh')
        user_id = token_data.get('user_id')
        user_data = self.fetch_data_for_key(user_id)
        if refresh_token == user_data.get('refresh_token'):
            return AccessToken(**token_data)
        raise AccessTokenNotFound()

    def delete_refresh_token(self, refresh_token):
        return self.delete_key(refresh_token, key_type='refresh')

    @classmethod
    def fetch_data_for_access_token(cls, access_token, return_type='dict', user_data_dict=None):
        token_data_dict = cls.fetch_data_for_key(access_token, key_type='access')
        user_id = token_data_dict.get('user_id')
        user_data = user_data_dict or cls.fetch_data_for_key(user_id)
        if user_data.get('token') == access_token:
            return cls.format_data_for_response(token_data_dict) \
                if return_type == 'dict' \
                else AccessToken(**token_data_dict)
        raise AccessTokenNotFound()

    @classmethod
    def fetch_data_for_key(cls, actual_key, key_type='user'):
        token_data = redis.get(cls.get_token_key(actual_key, key_type=key_type))
        if token_data:
            return literal_eval(token_data)
        raise AccessTokenNotFound()

    @classmethod
    def add_old_refresh_to_access_token(cls, access_token):
        token_data = cls.fetch_data_for_key(access_token.user_id)
        access_token.refresh_token = token_data.get('refresh_token')
        access_token.refresh_expires_at = int(time()) + REFRESH_TOKEN_REDIS_TTL

    @classmethod
    def delete_old_tokens_for_user(cls, user_id):
        try:
            user_data = cls.fetch_data_for_key(user_id)
            access_token, refresh_token = user_data.get('token'), user_data.get('refresh_token')
            cls.delete_key(access_token, key_type='access')
            cls.delete_key(refresh_token, key_type='refresh')
        except AccessTokenNotFound:
            return

    @classmethod
    def reset_existing_token_expiry(cls, existing_token):
        existing_token.expires_at = int(time()) + ACCESS_TOKEN_REDIS_TTL
        existing_token.refresh_expires_at = int(time()) + REFRESH_TOKEN_REDIS_TTL
        cls.save_keys_for_token(existing_token)

    @classmethod
    def delete_key(cls, actual_key, key_type='user'):
        return redis.delete(cls.get_token_key(actual_key, key_type=key_type))

    @classmethod
    def get_token_key(cls, actual_key, key_type='user'):
        return cls.token_key_prefix + '_' + key_type + '_' + actual_key

    @classmethod
    def save_keys_for_token(cls, access_token):
        redis.setex(cls.get_token_key(access_token.user_id),
                    access_token.__dict__,
                    REFRESH_TOKEN_REDIS_TTL)
        redis.setex(cls.get_token_key(access_token.token, key_type='access'),
                    access_token.__dict__,
                    ACCESS_TOKEN_REDIS_TTL)
        redis.setex(cls.get_token_key(access_token.refresh_token, key_type='refresh'),
                    access_token.__dict__,
                    REFRESH_TOKEN_REDIS_TTL)

    @classmethod
    def format_data_for_response(cls, data_dict):
        data_dict['expires_in'] = data_dict['expires_at'] - int(time())
        data_dict['refresh_expires_in'] = data_dict['refresh_expires_at'] - int(time())
        return dict((k, v) for k, v in data_dict.iteritems() if v and k not in fields_to_remove_from_response)
