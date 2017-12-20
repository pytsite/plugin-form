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


def plugin_load():
    from pytsite import lang
    from plugins import assetman

    lang.register_package(__name__)

    assetman.register_package(__name__)
    assetman.t_less(__name__)
    assetman.t_js(__name__)
    assetman.js_module('pytsite-form-module', __name__ + '@js/pytsite-form-module')


def plugin_load_uwsgi():
    from pytsite import router, tpl
    from plugins import http_api
    from . import _controllers, _http_api_controllers

    tpl.register_package(__name__)

    router.handle(_controllers.Submit, '/form/submit/<uid>', 'form@submit', methods='POST')

    http_api.handle('POST', 'form/widgets/<uid>', _http_api_controllers.GetWidgets, 'form@post_get_widgets')
    http_api.handle('POST', 'form/validate/<uid>', _http_api_controllers.PostValidate, 'form@post_validate')


def plugin_install():
    from plugins import assetman

    plugin_load()
    assetman.build(__name__)
    assetman.build_translations()
