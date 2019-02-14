"""PytSite Form Plugin Base Form
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

import re as _re
from typing import List as _List, Optional as _Optional, Mapping as _Mapping
from abc import ABC as _ABC, abstractmethod as _abstractmethod
from collections import OrderedDict as _OrderedDict
from datetime import datetime as _datetime
from math import ceil as _ceil
from pytsite import util as _util, router as _router, validation as _validation, tpl as _tpl, events as _events, \
    lang as _lang, reg as _reg, cache as _cache, http as _http, routing as _routing
from plugins import widget as _widget, http_api as _http_api
from . import _error

_CACHE_TTL = _reg.get('form.cache_ttl', 604800)  # 7 days
_F_NAME_SUB_RE = _re.compile('[^a-zA-Z0-9_]+')
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

        # Last widget's weight
        self._last_widget_weight = {k: 0 for k in self._areas}

        # Form's class ID
        self._cid = '{}.{}'.format(self.__module__, self.__class__.__name__)

        # Form's UID
        self._uid = None  # type: str

        # Current step
        self._current_step = 1

        # Should form be cached
        self._cache = False

        # Default submit button
        self._submit_button = _widget.button.Submit(
            weight=200,
            uid='action_submit',
            value=_lang.t('form@save'),
            color='primary',
            form_area='footer',
            css='form-action-submit',
            icon='fa fas fa-fw fa-check',
        )

        # Form's attributes. This dict holds all form's attributes that can be set from outside.
        # Using dict instead of separate object's properties motivated by large amount of variables and necessity of
        # caching them in convenient manner
        self._attrs = {
            'created': _datetime.now(),
            'name': '',
            'enctype': 'application/x-www-form-urlencoded',
            'method': 'post',
            'action': '',
            'data': {},
            'location': request.url,
            'referer': request.referrer,
            'redirect': self._request.inp.get('__redirect'),
            'steps': 1,
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
        }

        # Presence of '_uid' kwarg means that form's is being reconstructed by _api.dispense()
        if '_uid' in kwargs:
            self._uid = kwargs.pop('_uid')

            # Restore form's attributes from cache
            if self._attrs_cache.has(self._uid):
                self._cache = True
                self._attrs.update(self._attrs_cache.get_hash(self._uid))

            # This attributes must be overwritten
            for k in ('location', 'referer', 'redirect'):
                v = request.inp.get('__' + k)
                if v:
                    self.set_attr(k, v)

            # Perform form's setup
            self._on_setup_form()

            # Form setup event
            _events.fire('form@setup_form.' + self.name, frm=self)

        # Normal form initialization
        else:
            # Set attributes from kwargs
            for k, v in kwargs.items():
                self.set_attr(k, v)

            # Perform form's setup
            self._on_setup_form()

            # Set form's UID if it still not set
            if not self._uid:
                self._uid = self._build_uid()

            # Set form's name if it still not set
            if not self.name:
                self.name = _F_NAME_SUB_RE.sub('_', self._uid.lower()).replace('__', '_')

            # Set default action
            if not self.action:
                try:
                    self.action = _http_api.url('form@post_submit', {'__form_uid': self._uid})
                except _routing.error.RuleNotFound:
                    pass

            # Form setup event
            _events.fire('form@setup_form.' + self.name, frm=self)

            # Add convenient CSS classes
            self.css += ' form-cid-{}'.format(_CSS_SUB_RE.sub('-', self._cid.lower()).replace('--', '-'))

    def _build_uid(self) -> str:
        """Build form's UID
        """
        if self._cache:
            while True:
                uid = _util.random_password(8, True)
                if not self._cids_cache.has(uid):
                    break

            # Prepare cache
            self._cids_cache.put(uid, self._cid, _CACHE_TTL)
            self._attrs_cache.put_hash(uid, self._attrs, _CACHE_TTL)

            return uid
        else:
            return 'cid:{}'.format(self._cid)

    def setup_widgets(self):
        """Setup widgets
        """
        # 'Submit' button for the last step
        if self.steps == self._current_step and self._submit_button:
            self.add_widget(self._submit_button)

        # 'Next' button for all steps except the last one
        if self._current_step < self.steps:
            self.add_widget(_widget.button.Submit(
                weight=200,
                uid='action_forward_' + str(self._current_step + 1),
                value=_lang.t('form@forward'),
                form_area='footer',
                color='primary',
                css='form-action-forward',
                icon='fa fas fa-fw fa-forward',
                data={
                    'to-step': self._current_step + 1,
                }
            ))

        # 'Back' button for all steps except the first one
        if self._current_step > 1:
            self.add_widget(_widget.button.Button(
                weight=100,
                uid='action_backward_' + str(self._current_step - 1),
                value=_lang.t('form@backward'),
                form_area='footer',
                form_step=self._current_step,
                css='form-action-backward',
                icon='fa fas fa-fw fa-backward',
                data={
                    'to-step': self._current_step - 1,
                }
            ))

        # Ask form instance to setup widgets
        self._on_setup_widgets()

        # Ask others to setup form's widgets
        _events.fire('form@setup_widgets.' + self.name, frm=self)

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
        # First call of this method
        if not self._uid:
            self._uid = self._build_uid()

        if self._cache:
            self._attrs[k] = v
            self._attrs_cache.put_hash_item(self._uid, k, v)
        else:
            # Non-standard attributes can be stored only in cache
            if k not in self._attrs:
                self._cache = True
                self._attrs[k] = v

                # Regenerate form UID
                self._uid = self._build_uid()

                # Put existing attributes to cache
                self._attrs_cache.put_hash(self._uid, self._attrs, _CACHE_TTL)
            else:
                self._attrs[k] = v

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
        if 'pytsite-form' not in value:
            value += ' pytsite-form'

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
        if value < 1:
            value = 1

        if value > 1 and not self._cache:
            self._cache = True

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
    def location(self) -> str:
        """Get location URL
        """
        return self._attrs['location']

    @location.setter
    def location(self, value: str):
        """Set location URL
        """
        self.set_attr('location', value)

    @property
    def referer(self) -> str:
        """Get referer URL
        """
        return self._attrs['referer']

    @referer.setter
    def referer(self, value: str):
        """Set referer URL
        """
        self.set_attr('referer', value)

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
        r = _OrderedDict([(w.uid, w.get_val()) for w in self.get_widgets()])

        # Sometimes widgets can have different UID and name
        r.update(_OrderedDict([(w.name, w.get_val()) for w in self.get_widgets()]))

        return r

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

        # Fill widgets in order they placed on the form
        for widget in self.get_widgets(self._current_step):
            if widget.uid in values or widget.name in values:
                widget.value = values[widget.uid if widget.uid in values else widget.name]
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
            w.form_submit(self._request)

        # Notify form instance
        r = self._on_submit()

        # Clear cache
        if self._cache:
            self._attrs_cache.rm(self._uid)
            self._cids_cache.rm(self._uid)
            self._values_cache.rm(self._uid)

        return r

    def render(self) -> str:
        """Render the form
        """
        _events.fire('form@render.' + self.name, frm=self)

        return _tpl.render(self.tpl, {'form': self})

    def __str__(self) -> str:
        """Render the form
        """
        return self.render()

    def add_widget(self, widget: _widget.Abstract) -> _widget.Abstract:
        """Add a widget
        """
        if widget.form_area not in self._areas:
            raise ValueError("Invalid form area: {}".format(widget.form_area))

        if not widget.weight:
            self._last_widget_weight[widget.form_area] += 100
            widget.weight = self._last_widget_weight[widget.form_area]
        elif widget.weight > self._last_widget_weight[widget.form_area]:
            self._last_widget_weight[widget.form_area] = _ceil(widget.weight / 100) * 100

        self._widgets.append(widget)
        self._widgets.sort(key=lambda x: x.weight)

        return widget

    def replace_widget(self, source_uid: str, replacement: _widget.Abstract):
        """Replace a widget with another one
        """
        source = self.get_widget(source_uid)

        if source.parent:
            source.parent.replace_child(source_uid, replacement)
        else:
            if not replacement.weight and source.weight:
                replacement.weight = source.weight
            replacement.form_area = source.form_area
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

        :return: _List[_widget.Abstract]
        """
        r = []

        # Recursion depth > 0
        if _parent:
            # Add parent itself, optionally filter it
            if not filter_by or (filter_by and getattr(_parent, filter_by) == filter_val):
                r.append(_parent)

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
            return bool(self.get_widget(uid))
        except _error.WidgetNotExistError:
            return False

    def remove_widget(self, uid: str):
        """Remove widget from the form
        """
        w = self.get_widget(uid)
        w.clr_rules()

        if w.parent:
            w.parent.remove_child(w.uid)
        else:
            self._widgets = [w for w in self._widgets if w.uid != uid]

        return self

    def remove_widgets(self):
        """Remove all widgets
        """
        self._widgets = []

        return self

    @classmethod
    def get_package_name(cls) -> str:
        """Get instance's package name.
        """
        return '.'.join(cls.__module__.split('.')[:-1])

    @classmethod
    def resolve_msg_id(cls, partly_msg_id: str) -> str:
        # Searching for translation up in hierarchy
        for super_cls in cls.__mro__:
            if issubclass(super_cls, Form):
                full_msg_id = super_cls.get_package_name() + '@' + partly_msg_id
                if _lang.is_translation_defined(full_msg_id):
                    return full_msg_id

        return cls.get_package_name() + '@' + partly_msg_id

    @classmethod
    def t(cls, partial_msg_id: str, args: dict = None) -> str:
        """Translate a string in model context
        """
        return _lang.t(cls.resolve_msg_id(partial_msg_id), args)

    @classmethod
    def t_plural(cls, partial_msg_id: str, num: int = 2) -> str:
        """Translate a string into plural form.
        """
        return _lang.t_plural(cls.resolve_msg_id(partial_msg_id), num)
