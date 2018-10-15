from pyramid.config import Configurator

from .sessions import PVaultSessionFactory


def main(global_config, **settings):
    """This function returns a Pyramid WSGI application.

    This is the entrypoint of the application.
    """
    # Sessions Factory
    session_factory = PVaultSessionFactory(
        'seekrit',
        settings['hero_million.session.redis.host'],
        settings['hero_million.session.redis.port']
    )
    # Configurations
    config = Configurator(
        settings=settings,
        session_factory=session_factory
    )

    # Include external packages / modules
    config.include('pyramid_jinja2')

    # Include internal packages / modules
    config.include('.db')
    config.include('.routes')

    # Scan
    config.scan()
    return config.make_wsgi_app()
