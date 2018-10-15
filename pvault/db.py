"""Database configuration module.

In this module are declared the base class for every model of the application.

This module include the following packages in the config:
- pyramid_tm
- pyramid_retry

This module add the following request method:
- dbsession : return the dbsession.
"""
import sqlalchemy
from sqlalchemy import engine_from_config, inspect
from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy.schema import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm.exc import DetachedInstanceError

import zope.sqlalchemy

# ####### Old stuff from cookiecutter ############
# from .statistics.models.draw_number_model import DrawNumberModel
# run configure_mappers after defining all of the models to ensure
# all relationships can be setup
# configure_mappers()
# ################################################

# This come from the pyramid-cookiecutter-alchemy
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


# #############################################################################
# ########################## From Warehouse project ###########################
# #############################################################################
def make_repr(*attrs, _self=None):
    def _repr(self=None):
        if self is None and _self is not None:
            self = _self
        try:
            return "{}({})".format(
                self.__class__.__name__,
                ", ".join(
                    "{}={}".format(a, repr(getattr(self, a))) for a in attrs
                ),
            )
        except DetachedInstanceError:
            return "{}(<detached>)".format(self.__class__.__name__)

    return _repr


# class found in the pypa/warehouse project
class ModelBase:
    def __repr__(self):
        inst = inspect(self)
        self.__repr__ = make_repr(
            *[c_attr.key for c_attr in inst.mapper.column_attrs],
            _self=self,
        )
        return self.__repr__()


metadata = MetaData(naming_convention=NAMING_CONVENTION)
# Override the ModelBase class declare before.
# Now the base ModelBase is the Base class for all sqlalchemy model.
# pypa warehouse
ModelBase = declarative_base(cls=ModelBase, metadata=metadata)


# class found in the pypa/warehouse project
class Model(ModelBase):
    __abstract__ = True

    uuid = sqlalchemy.Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=sqlalchemy.text('gen_random_uuid()'),
    )
# #############################################################################
# #############################################################################

# This come from the pyramid-cookiecutter-alchemy
def _get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix)

def _get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory

def get_tm_session(session_factory, transaction_manager):
    """Get a ``sqlalchemy.orm.Session`` instance backed by a transaction.

    This function will hook the session to the transaction manager which
    will take care of committing any changes.

    - When using pyramid_tm it will automatically be committed or aborted
      depending on whether an exception is raised.

    - When using scripts you should wrap the session in a manager yourself.
      For example::

          import transaction

          engine = get_engine(settings)
          session_factory = get_session_factory(engine)
          with transaction.manager:
              dbsession = get_tm_session(session_factory, transaction.manager)
    """
    dbsession = session_factory()
    zope.sqlalchemy.register(
        dbsession, transaction_manager=transaction_manager
    )
    return dbsession

def includeme(config):
    """Initialize the model for a Pyramid app.

    Activate this setup using ``config.include('HeroMillions.models')``.
    """
    settings = config.get_settings()
    settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'

    # Include external packages / modules
    # use pyramid_tm to hook the transaction lifecycle to the request
    config.include('pyramid_tm')
    # use pyramid_retry to retry a request when transient exceptions occur
    config.include('pyramid_retry')

    # SQLAchemy stuff
    engine = _get_engine(settings)
    session_factory = _get_session_factory(engine)
    config.registry['dbsession_factory'] = session_factory

    # make request.dbsession available for use in Pyramid
    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        lambda r: get_tm_session(session_factory, r.tm),
        'dbsession',
        reify=True
    )
