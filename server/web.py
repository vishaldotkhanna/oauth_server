from tornado.ioloop import IOLoop
from tornado.web import url, Application
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from oauth2 import Provider
from oauth2.grant import ResourceOwnerGrant, RefreshToken
from oauth2.web.tornado import OAuth2Handler
from oauth2.tokengenerator import Uuid4
from auth_stores import AuthUserStore, AccessTokenStore, ACCESS_TOKEN_REDIS_TTL, REFRESH_TOKEN_REDIS_TTL
from oauth_handlers import AuthValidationHandler
from adapters import AuthSiteAdapter

import os


define('port', default=8008, type=int)
TEMPLATE_PATH = os.getcwd() + '/templates'
STATIC_PATH = os.getcwd() + '/static'
COOKIE_SECRET = 'foobar42'


def main():
    token_store = AccessTokenStore()
    provider = Provider(access_token_store=token_store,
                        auth_code_store=token_store,
                        client_store=AuthUserStore(),
                        token_generator=Uuid4())
    provider.add_grant(ResourceOwnerGrant(site_adapter=AuthSiteAdapter(),
                                          unique_token=True,
                                          expires_in=ACCESS_TOKEN_REDIS_TTL))
    provider.add_grant(RefreshToken(expires_in=REFRESH_TOKEN_REDIS_TTL))

    app = Application(handlers=[url(provider.token_path, OAuth2Handler, dict(provider=provider)),
                                url('/validate-token', AuthValidationHandler)],
                      template_path=TEMPLATE_PATH,
                      static_path=STATIC_PATH,
                      cookie_secret=COOKIE_SECRET)

    print 'Starting OAuth Server on port %d' % options.port
    server = HTTPServer(app)
    server.listen(options.port)
    IOLoop.current().start()

if __name__ == '__main__':
    main()
