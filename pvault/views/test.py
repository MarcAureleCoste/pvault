from pyramid.i18n import get_localizer
from pyramid.view import view_defaults, view_config
from pyramid.request import Request


@view_defaults(route_name='test')
class TestViews(object):
    def __init__(self, request:Request) -> None:
        self._request = request
        self._view_name = 'TestViews'
        self._next_url = self._get_next_url()
        self._dbsession = self._request.dbsession
        self._localizer = get_localizer(request)

    def _get_next_url(self) -> str:
        next_url = self._request.params.get('next', self._request.referrer)
        return next_url or self._request.route_url('test')

    @view_config(request_method='GET', renderer='../templates/test.jinja2')
    def test(self):
        return {}
