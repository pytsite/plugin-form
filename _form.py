"""PytSite Form Plugin Base Form
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

import re as _re
from typing import List as _List, Optional as _Optional, Mapping as _Mapping
from abc import ABC as _ABC, abstractmethod as _abstractmethod
from collections import OrderedDict as _OrderedDict
from datetime import datetime as _datetime
from pytsite import util as _util, router as _router, validation as _validation, tpl as _tpl, events as _events, \
    lang as _lang, routing as _routing, reg as _reg, cache as _cache
from plugins import widget as _widget, assetman as _assetman
from . import _error

_CACHE_TTL = _reg.get('form.cache_ttl', 86400)
_FORM_NAME_SUB_RE = _re.compile('[._]+')


class Form(_ABC):
    """Base Form
    """

    def __init__(self, **kwargs):
        """Init.
        """
        # Widgets
        self._widgets = []  # type: _List[_widget.Abstract]

        # Form areas where widgets can be placed
        self._areas = ('hidden', 'header', 'body', 'footer')

        # Areas CSS classes
        self._area_hidden_css = kwargs.get('area_hidden_css', '')
        self._area_header_css = kwargs.get('area_header_css', '')
        self._area_body_css = kwargs.get('area_body_css', '')
        self._area_footer_css = kwargs.get('area_footer_css', '')

        # Messages CSS
        self._messages_css = kwargs.get('messages_css', 'form-messages')

        self._cid = '{}.{}'.format(self.__module__, self.__class__.__name__)
        self._nocache = kwargs.get('nocache', False)

        if self._nocache:
            self._uid = 'cid:{}'.format(self._cid)
        else:
            self._uid = kwargs.get('uid', _util.random_password(alphanum_only=True))

        self._created = _datetime.now()
        self._name = kwargs.get('name', self._uid)
        self._path = kwargs.get('path')
        self._method = kwargs.get('method', 'post')
        self._action = kwargs.get('action')
        self._current_step = 1
        self._steps = int(kwargs.get('steps', 1))
        self._modal = kwargs.get('modal', False)
        self._modal_close_btn = kwargs.get('modal_close_btn', True)
        self._prevent_submit = kwargs.get('prevent_submit', False)
        self._redirect = kwargs.get('redirect')

        # Submit button
        self._submit_button = kwargs.get('submit_button', _widget.button.Submit(
            weight=20,
            uid='action-submit',
            value=_lang.t('form@save'),
            color='primary',
            icon='fa fa-fw fa-save',
            form_area='footer',
            css='form-action-submit',
        ))

        # AJAX endpoint to load form's widgets
        self._get_widgets_ep = kwargs.get('get_widgets_ep', 'form/widgets')

        # AJAX endpoint to perform form validation
        self._validation_ep = kwargs.get('validation_ep', 'form/validate')

        # Form template
        self._tpl = kwargs.get('tpl', 'form@form')

        # <form>'s tag CSS class
        self._css = str(kwargs.get('css', '') + ' pytsite-form').strip()
        self._css += ' form-name-{}'.format(self._name)

        # Title
        self._title = kwargs.get('title')
        self._hide_title = kwargs.get('hide_title', False)
        self._title_css = kwargs.get('title_css', '')

        # Attributes
        self._attrs = kwargs.get('attrs', {})

        # Set attributes from kwargs
        for k, v in kwargs.items():
            if k.startswith('attr_'):
                self._attrs[k.replace('attr_', '')] = v

        if not self._nocache:
            attrs_cache = _cache.get_pool('form.form_attrs')

            if not attrs_cache.has(self._uid):
                attrs_cache.put_hash(self._uid, {}, _CACHE_TTL)

            # Cache attributes which has been set from kwargs
            for k, v in self._attrs.items():
                attrs_cache.put_hash_item(self._uid, k, v)

            # Restore attributes from the cache
            for k, v in attrs_cache.get_hash(self._uid).items():
                if k not in self._attrs:
                    self._attrs[k] = v

        # Call setup hook
        self._on_setup_form(**kwargs)

        # Cache attributes after after calling _on_setup_form()
        if not self._nocache:
            attrs_cache = _cache.get_pool('form.form_attrs')

            if not attrs_cache.has(self._uid):
                attrs_cache.put_hash(self._uid, {}, _CACHE_TTL)

            for k, v in self._attrs.items():
                attrs_cache.put_hash_item(self._uid, k, v)

        # Assets
        if _router.request():
            _assetman.preload('form@css/form.css')
            _assetman.preload('form@js/pytsite-form.js')

        # Store form's class ID
        if not self._nocache:
            _cache.get_pool('form.form_cid').put(self._uid, self._cid, _CACHE_TTL)

    def setup_widgets(self):
        """Setup form's widgets.
        """
        # 'Submit' button for the last step
        if self._steps == self._current_step:
            if isinstance(self._submit_button, _widget.button.Submit):
                self.add_widget(self._submit_button)

        # 'Next' button for all steps except the last one
        if self._current_step < self._steps:
            self.add_widget(_widget.button.Submit(
                weight=20,
                uid='action-forward-' + str(self._current_step + 1),
                value=_lang.t('form@forward'),
                form_area='footer',
                color='primary',
                icon='fa fa-fw fa-forward',
                css='form-action-forward',
                data={
                    'to-step': self._current_step + 1,
                }
            ))

        # 'Back' button for all steps except the first one
        if self._current_step > 1:
            self.add_widget(_widget.button.Button(
                weight=10,
                uid='action-backward-' + str(self._current_step - 1),
                value=_lang.t('form@backward'),
                form_area='footer',
                form_step=self._current_step,
                icon='fa fa-fw fa-backward',
                css='form-action-backward',
                data={
                    'to-step': self._current_step - 1,
                }
            ))

        # Ask form instance to setup widgets
        self._on_setup_widgets()

        # Ask others to setup form's widgets
        _events.fire('form@setup_widgets.' + self.name.replace('-', '_'), frm=self)

        # Restore widgets' values
        if not self._nocache:
            try:
                for k, v in _cache.get_pool('form.form_values').get_hash(self._uid).items():
                    try:
                        self.get_widget(k).set_val(v)
                    except _error.WidgetNotExist:
                        pass
            except _cache.error.KeyNotExist:
                pass

        return self

    def _on_setup_form(self, **kwargs):
        """Hook.
        :param **kwargs:
        """
        pass

    @_abstractmethod
    def _on_setup_widgets(self):
        """Hook.
        """
        pass

    def _on_validate(self):
        """Hook.
        """
        pass

    def _on_submit(self):
        """Hook.
        """
        pass

    @property
    def areas(self) -> tuple:
        """Get form's areas.
        """
        return self._areas

    @property
    def uid(self) -> str:
        """Get form ID.
        """
        return self._uid

    @property
    def created(self) -> _datetime:
        return self._created

    @property
    def name(self) -> str:
        """Get form name.
        """
        return self._name

    @name.setter
    def name(self, value: str):
        """Set form name.
        """
        self._name = value

    @property
    def method(self) -> str:
        """Get method.
        """
        return self._method

    @method.setter
    def method(self, value):
        self._method = value

    @property
    def action(self) -> str:
        """Get form's action URL
        """
        if not self._action:
            try:
                self._action = _router.rule_url('form@submit', {'uid': self._uid})
            except _routing.error.RuleNotFound:
                self._action = _router.base_url()

        return _router.url(self._action, query={'__redirect': self.redirect}) if self.redirect else self._action

    @action.setter
    def action(self, value):
        """Set form's action URL
        """
        self._action = value

    @property
    def title(self) -> str:
        """Get title.
        """
        return self._title

    @title.setter
    def title(self, value: str):
        """Set title.
        """
        self._title = value

    @property
    def hide_title(self) -> bool:
        """Get hide_title.
        """
        return self._hide_title

    @hide_title.setter
    def hide_title(self, value: bool):
        """Set hide_title.
        """
        self._hide_title = value

    @property
    def css(self) -> str:
        """Get CSS classes.
        """
        return self._css

    @css.setter
    def css(self, value):
        """Set CSS classes.
        """
        self._css = value + ' pytsite-form' if 'pytsite-form' not in value else value

    @property
    def area_hidden_css(self) -> str:
        return self._area_hidden_css

    @property
    def area_header_css(self) -> str:
        return self._area_header_css

    @property
    def title_css(self) -> str:
        return self._title_css

    @property
    def messages_css(self) -> str:
        return self._messages_css

    @property
    def area_body_css(self) -> str:
        return self._area_body_css

    @area_body_css.setter
    def area_body_css(self, value: str):
        self._area_body_css = value

    @property
    def area_footer_css(self) -> str:
        return self._area_footer_css

    @area_footer_css.setter
    def area_footer_css(self, value: str):
        self._area_footer_css = value

    @property
    def get_widgets_ep(self) -> str:
        return self._get_widgets_ep

    @get_widgets_ep.setter
    def get_widgets_ep(self, val: str):
        self._get_widgets_ep = val

    @property
    def validation_ep(self) -> str:
        """Get validation endpoint.
        """
        return self._validation_ep

    @validation_ep.setter
    def validation_ep(self, value):
        """Set validation endpoint.
        """
        self._validation_ep = value

    @property
    def values(self) -> _OrderedDict:
        return _OrderedDict([(w.name, w.get_val()) for w in self.get_widgets()])

    @property
    def fields(self) -> list:
        """Get list of names of all widgets.
        """
        return [w.uid for w in self.get_widgets()]

    @property
    def steps(self) -> int:
        return self._steps

    @steps.setter
    def steps(self, value: int):
        self._steps = value

    @property
    def current_step(self) -> int:
        return self._current_step

    @current_step.setter
    def current_step(self, value: int):
        self._current_step = value

    @property
    def modal(self) -> bool:
        return self._modal

    @modal.setter
    def modal(self, value: bool):
        self._modal = value

    @property
    def modal_close_btn(self) -> bool:
        return self._modal_close_btn

    @modal_close_btn.setter
    def modal_close_btn(self, value: bool):
        self._modal_close_btn = value

    @property
    def prevent_submit(self) -> bool:
        return self._prevent_submit

    @prevent_submit.setter
    def prevent_submit(self, val: bool):
        self._prevent_submit = val

    @property
    def redirect(self) -> str:
        if self._redirect is None and _router.request() and '__redirect' in _router.request().inp:
            self._redirect = _router.request().inp.get('__redirect')

        return self._redirect

    @redirect.setter
    def redirect(self, val: str):
        self._redirect = val

    @property
    def attrs(self) -> dict:
        return self._attrs

    def attr(self, k: str, default=None):
        """Get form's attribute
        """
        return self._attrs.get(k, default)

    @property
    def path(self) -> str:
        if not self._path:
            self._path = _router.current_path(True)

        return self._path

    @property
    def nocache(self) -> bool:
        return self._nocache

    @nocache.setter
    def nocache(self, value: bool):
        self._nocache = value

        if self._nocache:
            self._uid = 'cid:{}'.format(self._cid)
            _cache.get_pool('form.form_attrs').rm(self._uid)
        else:
            self._uid = _util.random_password(alphanum_only=True)

    @property
    def submit_button(self) -> _Optional[_widget.button.Submit]:
        return self._submit_button

    @submit_button.setter
    def submit_button(self, value: _Optional[_widget.button.Submit]):
        if not (value in (None, False) or isinstance(value, _widget.button.Submit)):
            raise TypeError('None, False or {} expected, got {}'.format(type(_widget.button.Submit), value))

        self._submit_button = value

    def fill(self, values: _Mapping):
        """Fill form's widgets with values.
        """
        if not self._nocache:
            cache_pool = _cache.get_pool('form.form_values')
            try:
                cache_pool.get_hash(self._uid)
            except _cache.error.KeyNotExist:
                cache_pool.put_hash(self._uid, {}, _CACHE_TTL)

        for widget in self.get_widgets():  # type: _widget.Abstract
            if widget.name in values:
                widget.value = values[widget.name]
                if not self._nocache:
                    _cache.get_pool('form.form_values').put_hash_item(self._uid, widget.uid, widget.value)

        return self

    def add_rule(self, widget_uid: str, rule: _validation.rule.Rule):
        """Add a rule to the widget.
        """
        self.get_widget(widget_uid).add_rule(rule)

        return self

    def add_rules(self, widget_uid: str, rules: tuple):
        """Add multiple rules to the widgets.
        """
        for rule in rules:
            self.add_rule(widget_uid, rule)

        return self

    def remove_rules(self, widget_uid: str):
        """Remove validation's rules from the widget.
        """
        self.get_widget(widget_uid).clr_rules()

        return self

    def validate(self):
        """Validate the form.
        """
        errors = {}

        # Validate each widget
        for w in self.get_widgets():
            try:
                w.validate()
            except _validation.error.RuleError as e:
                if w.uid not in errors:
                    errors[w.uid] = []
                errors[w.uid].append(str(e))

        if errors:
            raise _error.ValidationError(errors)

        self._on_validate()

        return self

    def submit(self):
        """Should be called by endpoint when it processing form submit.
        """
        # Notify widgets
        for w in self._widgets:
            w.form_submit(self._uid)

        # Notify form instance
        r = self._on_submit()

        # Clear cache
        if not self._nocache:
            _cache.get_pool('form.form_attrs').rm(self._uid)
            _cache.get_pool('form.form_cid').rm(self._uid)
            _cache.get_pool('form.form_values').rm(self._uid)

        return r

    def render(self) -> str:
        """Render the form.
        """
        _events.fire('form@render.' + self.name.replace('-', '_'), frm=self)

        return _tpl.render(self._tpl, {'form': self})

    def __str__(self) -> str:
        """Render the form.
        """
        return self.render()

    def add_widget(self, widget: _widget.Abstract) -> _widget.Abstract:
        """Add a widget.
        """
        if widget.form_area not in self._areas:
            raise ValueError("Invalid form area: '{}'".format(widget.form_area))

        if widget.uid in self._widgets:
            raise KeyError("Widget '{}' is already added".format(widget.uid))

        self._widgets.append(widget)
        self._widgets.sort(key=lambda x: x.weight)

        return widget

    def replace_widget(self, source_uid: str, replacement: _widget.Abstract):
        """Replace a widget with another one.
        """
        current = self.get_widget(source_uid)
        if not replacement.weight and current.weight:
            replacement.weight = current.weight

        replacement.form_area = current.form_area
        replacement.replaces = source_uid

        self.remove_widget(source_uid).add_widget(replacement)

        return self

    def hide_widget(self, uid):
        """Hide a widget.
         """
        self.get_widget(uid).hide()

        return self

    def get_widgets(self, step: int = 1, filter_by: str = None, filter_val=None, _parent: _widget.Abstract = None):
        """Get widgets

        :rtype: _List[_widget.Abstract]
        """
        r = []

        # Recursion depth > 0
        if _parent:
            # Filter by some widget's attribute
            if not filter_by or (filter_by and getattr(_parent, filter_by) == filter_val):
                r.append(_parent)

            try:
                for widget in _parent.children:
                    r += self.get_widgets(step, filter_by, filter_val, widget)
            except NotImplementedError:
                pass

        # Recursion depth == 0
        else:
            for widget in self._widgets:
                r += self.get_widgets(step, filter_by, filter_val, widget)

        return r

    def get_widget(self, uid: str) -> _widget.Abstract:
        """Get a widget.
        """
        r = self.get_widgets(filter_by='uid', filter_val=uid)
        if not r:
            raise _error.WidgetNotExist("Widget '{}' does not exist.".format(uid))

        return r[0]

    def has_widget(self, uid: str) -> bool:
        """Check if the form has widget.
        """
        try:
            self.get_widget(uid)
            return True
        except _error.WidgetNotExist:
            return False

    def remove_widget(self, uid: str):
        """Remove widget from the form.
        """
        w = self.get_widget(uid)
        w.clr_rules()

        if w.parent:
            w.parent.remove_child(uid)
        else:
            self._widgets = [w for w in self._widgets if w.uid != uid]

        return self

    def remove_widgets(self):
        """Remove all added widgets.
        """
        self._widgets = []

        return self
