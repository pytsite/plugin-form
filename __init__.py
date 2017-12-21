"""Pytsite Form Plugin Plugin
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import plugman as _plugman

if _plugman.is_installed(__name__):
    # Public API
    from . import _error as error
    from ._form import Form


def _register_assetman_resources():
    from plugins import assetman

    if not assetman.is_package_registered(__name__):
        assetman.register_package(__name__)
        assetman.t_less(__name__)
        assetman.t_js(__name__)
        assetman.js_module('pytsite-form-module', __name__ + '@js/pytsite-form-module')

    return assetman


def plugin_install():
    _register_assetman_resources().build(__name__)


def plugin_load():
    _register_assetman_resources()


def plugin_load_uwsgi():
    from pytsite import router, tpl, lang
    from plugins import http_api
    from . import _controllers, _http_api_controllers

    lang.register_package(__name__)
    tpl.register_package(__name__)

    router.handle(_controllers.Submit, '/form/submit/<uid>', 'form@submit', methods='POST')

    http_api.handle('POST', 'form/widgets/<uid>', _http_api_controllers.GetWidgets, 'form@post_get_widgets')
    http_api.handle('POST', 'form/validate/<uid>', _http_api_controllers.PostValidate, 'form@post_validate')
