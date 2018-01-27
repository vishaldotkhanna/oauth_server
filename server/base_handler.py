from tornado.web import RequestHandler, HTTPError
import json


class BaseHandler(RequestHandler):
    def prepare_response(self, status='undefined', **kwargs):
        response_dict = dict(status=status, payload=kwargs)
        return json.dumps(response_dict, indent=4)


def authenticate_user(roles):
    def decorator(f):
        def inner_authorize(*args, **kwargs):
            roles_list = [roles] if type(roles) is not list else roles
            handler = args[0]
            current_user = handler.get_current_user_dict()
            if current_user.get('role') in roles_list:
                kwargs['current_user'] = current_user
                return f(*args, **kwargs)
            handler.redirect('/login')
        return inner_authorize
    return decorator


def authenticate_account_owner(f):
    def wrapper(*args, **kwargs):
        handler = args[0]
        account_id = int(args[1]) if len(args) > 1 else None
        current_user = kwargs.get('current_user') or handler.get_current_user_dict()
        if account_id and account_id == current_user.get('user_id'):
            return f(*args, **kwargs)
        raise HTTPError(401, 'Unauthorized Account Access')
    return wrapper
