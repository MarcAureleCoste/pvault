from pyramid.i18n import get_localizer
from pyramid.view import view_defaults, view_config
from pyramid.request import Request


@view_defaults(route_name='home')
class HomeViews(object):
    def __init__(self, request:Request) -> None:
        self._request = request
        self._view_name = 'HomeViews'
        self._next_url = self._get_next_url()
        self._dbsession = self._request.dbsession
        self._localizer = get_localizer(request)

    def _get_next_url(self) -> str:
        next_url = self._request.params.get('next', self._request.referrer)
        return next_url or self._request.route_url('home')

    @view_config(request_method='GET', renderer='../templates/home.jinja2')
    def home(self):
        return {'project': 'pvault'}
