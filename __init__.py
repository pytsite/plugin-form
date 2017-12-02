"""Pytsite Form Plugin Plugin
"""
# Public API
from . import _error as error
from ._form import Form

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


def _init():
    from pytsite import tpl, lang, router
    from plugins import assetman, http_api
    from . import _controllers, _http_api_controllers

    lang.register_package(__name__)
    tpl.register_package(__name__)

    assetman.register_package(__name__)
    assetman.t_less(__name__ + '@**')
    assetman.t_js(__name__ + '@**')
    assetman.js_module('pytsite-form-module', __name__ + '@js/pytsite-form-module')

    router.handle(_controllers.Submit, '/form/submit/<uid>', 'form@submit', methods='POST')

    http_api.handle('POST', 'form/widgets/<uid>', _http_api_controllers.GetWidgets, 'form@post_get_widgets')
    http_api.handle('POST', 'form/validate/<uid>', _http_api_controllers.PostValidate, 'form@post_validate')


_init()
