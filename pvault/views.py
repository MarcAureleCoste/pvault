from pyramid.view import view_config


@view_config(route_name='home', renderer='templates/home.jinja2')
def home_view(request):
    return {'project': 'pvault'}

@view_config(route_name='test', renderer='templates/test.jinja2')
def test_view(request):
    return {}

@view_config(route_name='test_session', renderer='templates/test_session.jinja2')
def test_session_view(request):
    session = request.session
    if 'counter' in session:
        session['counter'] += 1
    else:
        session['counter'] = 1
    session.flash("Counter updated", queue="success")
    return {'counter': session['counter']}
