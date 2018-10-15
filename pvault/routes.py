"""Entry routes for pvault application.

This file is include in the __init__. Here are the base routes of the
application like the root ('/').

Each subpackage have it's own routes module where are defined it's routes.
"""

def includeme(config):
    """Pyramid function that used to load module."""
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('test', '/test')
    config.add_route('test_session', '/testsession')
