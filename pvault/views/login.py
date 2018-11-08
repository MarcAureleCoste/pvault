from pyramid.i18n import get_localizer
from pyramid.view import view_defaults, view_config
from pyramid.request import Request

from nameko.standalone.rpc import ClusterRpcProxy


@view_defaults(route_name='login')
class LoginViews(object):
    def __init__(self, request: Request) -> None:
        self._request = request
        self._view_name = 'LoginViews'
        self._next_url = self._get_next_url()
        self._dbsession = self._request.dbsession
        self._localizer = get_localizer(request)

        self._config = {
            'AMQP_URI': 'pyamqp://guest:guest@localhost'
        }

    def _get_next_url(self) -> str:
        next_url = self._request.params.get('next', self._request.referrer)
        return next_url or self._request.route_url('login')

    @view_config(request_method='GET', renderer='../templates/login.jinja2')
    def login_page(self):
        return {
            'url': self._request.route_url('login'),
            'next_url': self._next_url
        }

    @view_config(request_method='POST', renderer='../templates/login.jinja2')
    def login(self):
        # Get data from the form and call the nameko service.
        email = self._request.params.get('email', None)
        password = self._request.params.get('password', None)
        with ClusterRpcProxy(self._config) as cluster_rpc:
            result = cluster_rpc.identity.login(email, password)
        return {'result': result}
