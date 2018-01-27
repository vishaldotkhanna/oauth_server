from tornado.ioloop import IOLoop
from tornado.web import url, Application, HTTPError
from tornado.httpserver import HTTPServer
from tornado.options import define, options
import requests
import json

from base_handler import BaseHandler


OAUTH_SERVER_URL = 'http://127.0.0.1:8008'
define('port', default=8081, type=int)


class WebServiceHandler(BaseHandler):
    def post(self, account_id, *args, **kwargs):
        access_token = self.request.headers.get('Access-Token', '')
        resp = requests.get(OAUTH_SERVER_URL + '/validate-token?access_token=' + access_token)
        if resp.status_code == 200:
            try:
                resp_dict = json.loads(resp.text)
                payload = resp_dict.get('status'), resp_dict.get('payload', {})
                resp_account_id = payload[1].get('data', {}).get('account_id')
                if resp_account_id == account_id:
                    self.write('OAuth Validation Successful.')
                    return
                raise HTTPError(401, reason='Invalid or Incorrect Account ID')
            except Exception as e:
                print 'Exception {} raised while parsing OAuth Validation response.'.format(str(e))
                raise HTTPError(400, reason='Unknown Error Occurred')
        raise HTTPError(401, reason='Invalid or Expired Access Token')


def main():
    app = Application(handlers=[url('/([0-9]+)/verify-oauth', WebServiceHandler)])
    print 'Starting Web Service on port %d' % options.port
    server = HTTPServer(app)
    server.listen(options.port)
    IOLoop.current().start()

if __name__ == '__main__':
    main()
