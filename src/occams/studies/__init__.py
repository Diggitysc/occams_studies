from __future__ import unicode_literals
import logging
import pkg_resources

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from repoze.who.config import make_middleware_with_config
from sqlalchemy.orm import scoped_session, sessionmaker
import zope.sqlalchemy

import occams.datastore.models.events

__version__ = pkg_resources.require(__name__)[0].version

_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)

Session = scoped_session(sessionmaker(
    extension=zope.sqlalchemy.ZopeTransactionExtension()))
occams.datastore.models.events.register(Session)

from .models import groups, RootFactory, groupfinder  # NOQA


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    config = Configurator(
        settings=settings,
        root_factory=RootFactory,
        authentication_policy=WhoV2AuthenticationPolicy(
            settings['who.config_file'],
            settings['who.identifier_id'],
            groupfinder),
        authorization_policy=ACLAuthorizationPolicy())

    # Required third-party plugins
    config.include('pyramid_chameleon')
    config.include('pyramid_mailer')
    config.include('pyramid_redis')
    config.include('pyramid_redis_sessions')
    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')
    config.include('pyramid_tm')
    config.include('pyramid_webassets')

    # Required second-party plugins
    config.include(settings['pid.package'])

    # App-specific configurations
    config.include('.assets')
    config.include('.links')
    config.include('.models')
    config.include('.routes')
    config.include('.tasks')

    config.scan()
    config.commit()

    app = config.make_wsgi_app()

    # Use repoze middleware to refresh the cookie after each request.
    # This will ensure timout/reissue_time settings are observed.
    app = make_middleware_with_config(
        app, global_config, settings['who.config_file'])

    log.info('Ready')

    return app
