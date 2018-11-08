import json

from pyramid.i18n import get_localizer
from pyramid.view import view_defaults, view_config
from pyramid.request import Request

from nameko.rpc import RpcProxy
from nameko.standalone.rpc import ClusterRpcProxy


@view_defaults(route_name='register')
class RegisterViews(object):
    def __init__(self, request:Request) -> None:
        self._request = request
        self._view_name = 'RegisterViews'
        self._next_url = self._get_next_url()
        self._dbsession = self._request.dbsession
        self._localizer = get_localizer(request)
        self._identity_rpc = RpcProxy('identity')

        self._config = {
            'AMQP_URI': 'pyamqp://guest:guest@localhost'
        }

    def _get_next_url(self) -> str:
        next_url = self._request.params.get('next', self._request.referrer)
        return next_url or self._request.route_url('home')

    @view_config(request_method='GET', renderer='../templates/register.jinja2')
    def register_page(self):
        # Get data from the form and call the nameko service.
        return dict(
            url=self._request.route_url('register'),
            next_url=self._next_url,
        )

    @view_config(request_method='POST', renderer='../templates/register.jinja2')
    def register(self):
        # Get data from the form and call the nameko service.
        username = self._request.params.get('username')
        lastname = self._request.params.get('lastname')
        firstname = self._request.params.get('firstname')
        email = self._request.params.get('email')
        password = self._request.params.get('password')
        # result = self._identity_rpc.register(email, password, username, firstname, lastname)
        with ClusterRpcProxy(self._config) as cluster_rpc:
            result = cluster_rpc.identity.register(email, password, username, firstname, lastname)
        result_dict = json.loads(result)
        return result_dict
