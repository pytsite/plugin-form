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
    lang as _lang, reg as _reg, cache as _cache, http as _http
from plugins import widget as _widget, assetman as _assetman
from . import _error

_CACHE_TTL = _reg.get('form.cache_ttl', 604800)  # 7 days
_CSS_SUB_RE = _re.compile('[^a-zA-Z0-9\-]+')


class Form(_ABC):
    """Base Form
    """

    def __init__(self, request: _http.Request, **kwargs):
        """Init
        """
        # Request
        self._request = request

        # Cache pools
        self._cids_cache = _cache.get_pool('form.form_cid')
        self._attrs_cache = _cache.get_pool('form.form_attrs')
        self._values_cache = _cache.get_pool('form.form_values')

        # Widgets
        self._widgets = []  # type: _List[_widget.Abstract]

        # Form's areas where widgets can be placed
        self._areas = ('hidden', 'header', 'body', 'footer')

        # Form's class ID
        self._cid = '{}.{}'.format(self.__module__, self.__class__.__name__)

        # Default form's UID
        self._uid = 'cid:{}'.format(self._cid)

        # Current step
        self._current_step = 1

        # If the form should be cached
        self._cache = False

        # Default submit button
        self._submit_button = _widget.button.Submit(
            weight=20,
            uid='action_submit',
            value=_lang.t('form@save'),
            color='primary',
            form_area='footer',
            css='form-action-submit',
        )

        # Attributes
        self._attrs = kwargs.get('attrs', {})
        self._attrs.update({
            'created': _datetime.now(),
            'name': '',
            'enctype': 'application/x-www-form-urlencoded',
            'method': 'post',
            'action': '',
            'data': {},
            'path': _router.current_path(),
            'redirect': self._request.inp.get('__redirect', '') if self._request else '',
            'steps': 1,
            'modal': False,
            'modal_close_btn': True,
            'prevent_submit': False,
            'update_location_hash': False,
            'css': 'pytsite-form',
            'area_hidden_css': '',
            'area_header_css': '',
            'area_body_css': '',
            'area_footer_css': '',
            'messages_css': 'form-messages',
            'get_widgets_ep': 'form/widgets',
            'validation_ep': 'form/validate',
            'tpl': 'form@form',
            'title': '',
            'hide_title': False,
            'title_css': '',
            'assets': ['form@css/form.css', 'form@js/pytsite-form.js']
        })

        # Presence of '_uid' kwarg means that form's is being reconstructed by _api.dispense().
        # If form's UID shows that form was cached, it must be tried to restore form's attributes from cache.
        if '_uid' in kwargs:
            self._uid = kwargs.pop('_uid')
            self._cache = True

            # Restore form's attributes from cache
            if self._attrs_cache.has(self._uid):
                self._attrs.update(self._attrs_cache.get_hash(self._uid))

        # Normal form initialization
        else:
            # Set attributes from kwargs
            for k, v in kwargs.items():
                self.set_attr(k, v)

            # Ask form to perform setup
            self._on_setup_form()

            # Check if the form must be cached after execution of self._on_setup_form() hook
            if self.steps > 1 and not self._cache:
                self._cache = True
                for k, v in self._attrs.items():
                    self.set_attr(k, v)

            # Set default action
            if not self.action:
                self.action = _router.rule_url('form@submit', {'__form_uid': self._uid})

            # Set default name
            if not self.name:
                self.name = self._uid

            # Add convenient CSS classes
            self.css += ' form-cid-{}'.format(_CSS_SUB_RE.sub('-', self._cid.lower()).replace('--', '-'))

    def setup_widgets(self):
        """Setup widgets
        """
        # 'Submit' button for the last step
        if self.steps == self._current_step and self._submit_button:
            self.add_widget(self._submit_button)

        # 'Next' button for all steps except the last one
        if self._current_step < self.steps:
            self.add_widget(_widget.button.Submit(
                weight=20,
                uid='action_forward_' + str(self._current_step + 1),
                value=_lang.t('form@forward'),
                form_area='footer',
                color='primary',
                css='form-action-forward',
                data={
                    'to-step': self._current_step + 1,
                }
            ))

        # 'Back' button for all steps except the first one
        if self._current_step > 1:
            self.add_widget(_widget.button.Button(
                weight=10,
                uid='action_backward_' + str(self._current_step - 1),
                value=_lang.t('form@backward'),
                form_area='footer',
                form_step=self._current_step,
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
        if self._cache:
            try:
                for k, v in _cache.get_pool('form.form_values').get_hash(self._uid).items():
                    try:
                        self.get_widget(k).set_val(v)
                    except _error.WidgetNotExistError:
                        pass
            except _cache.error.KeyNotExist:
                pass

        return self

    def _on_setup_form(self):
        """Hook
        """
        pass

    @_abstractmethod
    def _on_setup_widgets(self):
        """Hook
        """
        pass

    def _on_validate(self):
        """Hook
        """
        pass

    def _on_submit(self):
        """Hook
        """
        pass

    def set_attr(self, k: str, v):
        # If attribute is non-standard and form is not intended ot be cached,
        # mark form as "cached" and update its UID
        if k not in self._attrs and not self._cache:
            self._cache = True
            self._uid = _util.random_password(64, True)
            self._cids_cache.put(self._uid, self._cid, _CACHE_TTL)
            self._attrs_cache.put_hash(self._uid, self._attrs, _CACHE_TTL)

        if k == 'css' and 'pytsite-form' not in v:
            v += ' pytsite-form'

        self._attrs[k] = v

        if self._cache:
            self._attrs_cache.put_hash_item(self._uid, k, v)

    @property
    def request(self) -> _http.Request:
        """Get HTTP request instance
        """
        return self._request

    @property
    def areas(self) -> tuple:
        """Get areas
        """
        return self._areas

    @property
    def uid(self) -> str:
        """Get UID
        """
        return self._uid

    @property
    def created(self) -> _datetime:
        """Get time form created
        """
        return self._attrs['created']

    @property
    def name(self) -> str:
        """Get name
        """
        return self._attrs['name']

    @name.setter
    def name(self, value: str):
        """Set name
        """
        self.set_attr('name', value)

    @property
    def enctype(self) -> str:
        """Get enctype
        """
        return self._attrs['enctype']

    @enctype.setter
    def enctype(self, value: str):
        """Set enctype
        """
        self.set_attr('enctype', value)

    @property
    def method(self) -> str:
        """Get action's method
        """
        return self._attrs['method']

    @method.setter
    def method(self, value):
        """Set action's method
        """
        self.set_attr('method', value)

    @property
    def action(self) -> str:
        """Get action's URL
        """
        v = self._attrs['action']

        if v and self.redirect:
            v = _router.url(v, query={'__redirect': self.redirect})

        return v

    @action.setter
    def action(self, value):
        """Set action's URL
        """
        self.set_attr('action', value)

    @property
    def title(self) -> str:
        """Get title
        """
        return self._attrs['title']

    @title.setter
    def title(self, value: str):
        """Set title
        """
        self.set_attr('title', value)

    @property
    def hide_title(self) -> bool:
        """Check if the title should be hidden
        """
        return self._attrs['hide_title']

    @hide_title.setter
    def hide_title(self, value: bool):
        """Set if the title should be hidden
        """
        self.set_attr('hide_title', value)

    @property
    def css(self) -> str:
        """Get CSS classes
        """
        return self._attrs['css']

    @css.setter
    def css(self, value):
        """Set CSS classes
        """
        self.set_attr('css', value)

    @property
    def area_hidden_css(self) -> str:
        """Get hidden area CSS classes
        """
        return self._attrs['area_hidden_css']

    @area_hidden_css.setter
    def area_hidden_css(self, value):
        """Set hidden area CSS classes
        """
        self.set_attr('area_hidden_css', value)

    @property
    def area_header_css(self) -> str:
        """Get header area CSS classes
        """
        return self._attrs['area_header_css']

    @area_header_css.setter
    def area_header_css(self, value):
        """Set header area CSS classes
        """
        self.set_attr('area_header_css', value)

    @property
    def area_body_css(self) -> str:
        """Get body area CSS classes
        """
        return self._attrs['area_body_css']

    @area_body_css.setter
    def area_body_css(self, value: str):
        """Set body area CSS classes
        """
        self.set_attr('area_body_css', value)

    @property
    def area_footer_css(self) -> str:
        """Get footer area CSS classes
        """
        return self._attrs['area_footer_css']

    @area_footer_css.setter
    def area_footer_css(self, value: str):
        """Set footer area CSS classes
        """
        self.set_attr('area_footer_css', value)

    @property
    def title_css(self) -> str:
        """Get title CSS classes
        """
        return self._attrs['title_css']

    @title_css.setter
    def title_css(self, value):
        """Set title CSS classes
        """
        self.set_attr('title_css', value)

    @property
    def messages_css(self) -> str:
        """Get messages area CSS classes
        """
        return self._attrs['messages_css']

    @messages_css.setter
    def messages_css(self, value: str):
        """Set messages area CSS classes
        """
        self.set_attr('messages_css', value)

    @property
    def get_widgets_ep(self) -> str:
        """Get widgets retrieving HTTP API endpoint
        """
        return self._attrs['get_widgets_ep']

    @get_widgets_ep.setter
    def get_widgets_ep(self, value: str):
        """Set widgets retrieving HTTP API endpoint
        """
        self.set_attr('get_widgets_ep', value)

    @property
    def validation_ep(self) -> str:
        """Get validation HTTP API endpoint
        """
        return self._attrs['validation_ep']

    @validation_ep.setter
    def validation_ep(self, value: str):
        """Set validation HTTP API endpoint
        """
        self.set_attr('validation_ep', value)

    @property
    def steps(self) -> int:
        """Get number of form's steps
        """
        return self._attrs['steps']

    @steps.setter
    def steps(self, value: int):
        """Set number of form's steps
        """
        self.set_attr('steps', value)

    @property
    def current_step(self) -> int:
        """Get current step number
        """
        return self._current_step

    @current_step.setter
    def current_step(self, value: int):
        """Set current step number
        """
        self._current_step = value

    @property
    def modal(self) -> bool:
        """Check if the form is modal
        """
        return self._attrs['modal']

    @modal.setter
    def modal(self, value: bool):
        """Set if the form is modal
        """
        self.set_attr('modal', value)

    @property
    def modal_close_btn(self) -> bool:
        """Check if the form has modal's close button
        """
        return self._attrs['modal_close_btn']

    @modal_close_btn.setter
    def modal_close_btn(self, value: bool):
        """Set if the form has modal's close button
        """
        self.set_attr('modal_close_btn', value)

    @property
    def prevent_submit(self) -> bool:
        """Check if the form should prevent submitting by pressing the 'Submit' button
        """
        return self._attrs['prevent_submit']

    @prevent_submit.setter
    def prevent_submit(self, value: bool):
        """Set if the form should prevent submitting by pressing the 'Submit' button
        """
        self.set_attr('prevent_submit', value)

    @property
    def redirect(self) -> str:
        """Get redirect URL
        """
        return self._attrs['redirect']

    @redirect.setter
    def redirect(self, value: str):
        """Set redirect URL
        """
        self.set_attr('redirect', value)

    @property
    def update_location_hash(self) -> bool:
        """Check if the form should update browser's location hash
        """
        return self._attrs['update_location_hash']

    @update_location_hash.setter
    def update_location_hash(self, value: bool):
        """Set if the form should update browser's location hash
        """
        self.set_attr('update_location_hash', value)

    @property
    def data(self) -> dict:
        """Get data-attributes
        """
        return self._attrs['data']

    @property
    def assets(self) -> list:
        """Get assets list
        """
        return self._attrs['assets']

    @data.setter
    def data(self, value: dict):
        """Set data-attributes
        """
        self.set_attr('data', value)

    def attr(self, k: str, default=None):
        """Get attribute
        """
        return self._attrs.get(k, default)

    @property
    def path(self) -> str:
        """Get form's path
        """
        return self._attrs['path']

    @property
    def tpl(self) -> str:
        """Get form's tpl
        """
        return self._attrs['tpl']

    @tpl.setter
    def tpl(self, value: str):
        """Get form's tpl
        """
        self.set_attr('tpl', value)

    @property
    def submit_button(self) -> _Optional[_widget.button.Submit]:
        return self._submit_button

    @submit_button.setter
    def submit_button(self, value: _Optional[_widget.button.Submit]):
        if not (value in (None, False) or isinstance(value, _widget.button.Submit)):
            raise TypeError('None, False or {} expected, got {}'.format(type(_widget.button.Submit), value))

        self._submit_button = value

    @property
    def values(self) -> _OrderedDict:
        """Get form's values
        """
        return _OrderedDict([(w.name, w.get_val()) for w in self.get_widgets()])

    @property
    def fields(self) -> list:
        """Get list of names of widgets
        """
        return [w.uid for w in self.get_widgets()]

    def fill(self, values: _Mapping):
        """Fill form's widgets with values
        """
        # Create form's cache placeholder
        if self._cache:
            try:
                self._values_cache.get_hash(self._uid)
            except _cache.error.KeyNotExist:
                self._values_cache.put_hash(self._uid, {}, _CACHE_TTL)

        for k, v in values.items():
            # Try to fill widget by UID
            try:
                widget = self.get_widget(k)
                widget.value = v
                if self._cache:
                    self._values_cache.put_hash_item(self._uid, widget.uid, widget.value)

            # Fill widgets with appropriate names
            except _error.WidgetNotExistError:
                for widget in self.get_widgets(self._current_step, 'name', v):  # type: _widget.Abstract
                    widget.value = v
                    if self._cache:
                        self._values_cache.put_hash_item(self._uid, widget.uid, widget.value)

        return self

    def add_rule(self, widget_uid: str, rule: _validation.rule.Rule):
        """Add an validation rule
        """
        self.get_widget(widget_uid).add_rule(rule)

        return self

    def add_rules(self, widget_uid: str, rules: tuple):
        """Add multiple validation rules
        """
        for rule in rules:
            self.add_rule(widget_uid, rule)

        return self

    def remove_rules(self, widget_uid: str):
        """Remove validation's rules
        """
        self.get_widget(widget_uid).clr_rules()

        return self

    def validate(self):
        """Validate the form
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
            raise _error.FormValidationError(errors)

        self._on_validate()

        return self

    def submit(self):
        """Should be called by endpoint when it processing form submit
        """
        # Notify widgets
        for w in self._widgets:
            w.form_submit(self._uid)

        # Notify form instance
        r = self._on_submit()

        if not r and (self.redirect or self._request):
            r = _http.RedirectResponse(self.redirect or self._request.referrer)

        # Clear cache
        if self._cache:
            self._attrs_cache.rm(self._uid)
            self._cids_cache.rm(self._uid)
            self._values_cache.rm(self._uid)

        return r

    def render(self) -> str:
        """Render the form
        """
        _events.fire('form@render.' + self.name.replace('-', '_'), frm=self)

        return _tpl.render(self.tpl, {'form': self})

    def __str__(self) -> str:
        """Render the form
        """
        return self.render()

    def add_widget(self, widget: _widget.Abstract) -> _widget.Abstract:
        """Add a widget
        """
        if widget.form_area not in self._areas:
            raise ValueError("Invalid form area: '{}'".format(widget.form_area))

        if widget.uid in self._widgets:
            raise KeyError("Widget '{}' is already added".format(widget.uid))

        self._widgets.append(widget)
        self._widgets.sort(key=lambda x: x.weight)

        return widget

    def replace_widget(self, source_uid: str, replacement: _widget.Abstract):
        """Replace a widget with another one
        """
        current = self.get_widget(source_uid)
        if not replacement.weight and current.weight:
            replacement.weight = current.weight

        replacement.form_area = current.form_area
        replacement.replaces = source_uid

        self.remove_widget(source_uid).add_widget(replacement)

        return self

    def hide_widget(self, uid):
        """Hide a widget
         """
        self.get_widget(uid).hide()

        return self

    def get_widgets(self, step: int = 1, filter_by: str = None, filter_val=None, _parent: _widget.Abstract = None):
        """Get flat list of widgets

        :rtype: _List[_widget.Abstract]
        """
        r = []

        # Recursion depth > 0
        if _parent:
            # Add parent itself, optionally filter it
            if not filter_by or (filter_by and getattr(_parent, filter_by) == filter_val):
                r.append(_parent)

            if isinstance(_parent, _widget.Container):
                for widget in _parent.children:
                    r += self.get_widgets(step, filter_by, filter_val, widget)

        # Recursion depth == 0
        else:
            for widget in self._widgets:
                r += self.get_widgets(step, filter_by, filter_val, widget)

        return r

    def get_widget(self, uid: str) -> _widget.Abstract:
        """Get a widget
        """
        r = self.get_widgets(filter_by='uid', filter_val=uid)
        if not r:
            raise _error.WidgetNotExistError(uid)

        return r[0]

    def val(self, uid: str):
        """Get widget's value
        """
        return self.get_widget(uid).value

    def has_widget(self, uid: str) -> bool:
        """Check if the form has widget
        """
        try:
            self.get_widget(uid)
            return True
        except _error.WidgetNotExistError:
            return False

    def remove_widget(self, uid: str):
        """Remove widget from the form
        """
        w = self.get_widget(uid)
        w.clr_rules()

        if w.parent:
            w.parent.remove_child(uid)
        else:
            self._widgets = [w for w in self._widgets if w.uid != uid]

        return self

    def remove_widgets(self):
        """Remove all widgets
        """
        self._widgets = []

        return self
