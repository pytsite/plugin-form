"""Pytsite Form Plugin Plugin
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

# Public API
from ._api import on_setup_form, on_setup_widgets, on_render
from ._form import Form
from ._error import FormValidationError, WidgetNotExistError


def plugin_load():
    from pytsite import tpl, lang, cache
    from plugins import assetman

    lang.register_package(__name__)
    tpl.register_package(__name__)

    cache.create_pool('form.form_cid')
    cache.create_pool('form.form_attrs')
    cache.create_pool('form.form_values')

    assetman.register_package(__name__)
    assetman.js_module('pytsite-form-module', __name__ + '@js/pytsite-form-module')
    assetman.t_less(__name__)
    assetman.t_js(__name__, babelify=True)


def plugin_install():
    from plugins import assetman

    assetman.build(__name__)


def plugin_load_wsgi():
    from plugins import http_api, assetman
    from . import _http_api_controllers

    http_api.handle('POST', 'form/widgets/<__form_uid>/<__form_step>', _http_api_controllers.PostGetWidgets,
                    'form@post_get_widgets')
    http_api.handle('POST', 'form/validate/<__form_uid>/<__form_step>', _http_api_controllers.PostValidate,
                    'form@post_validate')
    http_api.handle('POST', 'form/submit/<__form_uid>', _http_api_controllers.PostSubmit,
                    'form@post_submit')

    assetman.preload(__name__ + '@js/pytsite-form.js', True)
