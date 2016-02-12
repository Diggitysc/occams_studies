import json

from . import log


def includeme(config):
    file = config.registry.settings.get('suite.file')
    apps = None
    if file:
        with open(file) as fp:
            apps = json.load(fp)
    config.add_request_method(lambda r: apps, name='apps', reify=True)
    log.debug('External app listing configured.')