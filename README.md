# PytSite Form Plugin


## Changelog


### 5.2 (2018-10-22)

Support of `assetman-5.x` and `widget-4.x`.


### 5.1 (2018-10-12)

Support of `assetman-4.x`.


### 5.0 (2018-10-11)

Support of `pytsite-8.x` and `widget-3.x`.


### 4.14.2 (2018-09-20)

Unwanted submit button enabling fixed.


### 4.14.1 (2018-09-09)

Setting of `location`, `referer` and `redirect` attributes fixed.


### 4.14 (2018-09-09)

New properties in `Form`: `location` and `referer`.


### 4.13.2 (2018-09-02)

Widgets order enforcement in `fill()` fixed.


### 4.13.1 (2018-08-29)

Form setup events order fixed.


### 4.13 (2018-08-21)

Support of `widget-2.11`.


### 4.12.3 (2018-08-21)

Setting of form's HTML ID fixed.


### 4.12.2 (2018-08-17)

String checking error fixed.


### 4.12.1 (2018-08-17)

Support of form's `GET` method fixed.


### 4.12 (2018-08-08)

Fixed and refactored.


### 4.11.1 (2018-08-05)

Typos fixed.


### 4.11 (2018-08-05)

Support of `widget-2.7`.


### 4.10 (2018-07-30)

New API functions: `on_setup_form()`, `on_setup_widgets()`,
`on_render()`.


### 4.9 (2018-07-30)

Form setup event added.


### 4.8 (2018-07-30)

Forms redirection refactored.


### 4.7 (2018-07-29)

- Support of `widget-2.4`.
- New methods in `Form`: `t()` and `t_plural()`.


### 4.6.3 (2018-07-22)

Icons fix.


### 4.6.2 (2018-07-21)

CSS fix.


### 4.6.1 (2018-07-21)

Support of Twitter Bootstrap 4 fixed.


### 4.6 (2018-07-19)

- `Form.prevent_submit` property removed.
- Support for `__reset` and `__alert` properties in submit response.


### 4.5 (2018-07-16)

- Default form submit handler moved to HTTP API.
- Form's widgets loading progress bar removed.


### 4.4.3 (2018-07-09)

Multiple forms widgets IDs overlapping issue fixed.


### 4.4.2 (2018-07-07)

Non-standard form attributes caching fixed.


### 4.4.1 (2018-07-07)

Form name set from kwargs fixed.


### 4.4 (2018-07-07)

- Caching issues fixed.
- Form name generation issue fixed.
- `Form.modal*` properties removed.


### 4.3.1 (2018-06-22)

Font Awesome's dependency removed.


### 4.3 (2018-06-06)

Support for `enctype` HTML attribute.


### 4.2.1 (2018-05-14)

JS code loading issue fixed.


### 4.2 (2018-05-14)

Form assets loading moved to JS code.


### 4.1 (2018-05-13)

- `Form.assets` property added.
- Additional CSS classes for form's areas added.
- `Form.attrs` property removed.


### 4.0 (2018-05-06)

- `Form.__init__()` signature changed.
- Caching issues fixed.
- New method: `Form.set_attr()`.
- `errors` module removed from the public API.
- New classes exposed to the public API: `FormValidationError`,
  `WidgetNotExistError`.


### 3.0.2 (2018-04-26)

Form's HTML class name building fixed.


### 3.0.1 (2018-04-26)

Form's CID now appends to the form's HTML class name.


### 3.0 (2018-04-25)

- Forms caching issues fixed.
- Forms attributes handling changed.


### 2.5 (2018-04-11)

`Form.nocache` setter disabled.


### 2.4.2 (2018-04-10)

Redirects and caching fixes.


### 2.4.1 (2018-04-10)

`Form.redirect` property getter fixed.


### 2.4 (2018-04-08)

- Form's UID checking added.
- Form's UID length increased to 64.


### 2.3.1 (2018-04-07)

Checkboxes serialization JS code fixed.


### 2.3 (2018-04-04)

- Support for form's HTML element data-attributes added.
- New method `Form.val()` added.
- `Form.fill()`'s logic changed a bit.


### 2.2 (2018-03-30)

Support for `widget-1.8`.


### 2.1 (2018-03-18)

New property added: `form.update_location_hash`.


### 2.0.2 (2018-03-15)

`Form`'s init code fixed.


### 2.0.1 (2018-03-15)

`Form`'s init code fixed.


### 2.0 (2018-03-15)

Totally reworked.


### 1.5.1 (2018-03-09)

Incorrect behaviour of `Form.redirect` property fixed.


### 1.5 (2018-03-08)

Little support of Twitter Bootstrap 4 added.


### 1.4.1 (2018-03-08)

Dependency of `Form` from `router.request()` readiness made optional.


### 1.4 (2018-02-21)

New property `Form.submit_button` and corresponding `Form`'s constructor
argument added.


### 1.3 (2017-12-27)

New property `Form.hide_title` added


### 1.2.2 (2017-12-21)

Init code refactored.


### 1.2.1 (2017-12-20)

Init code refactored.


### 1.2 (2017-12-13)

Support for PytSite-7.0.


### 1.1.1 (2017-12-05)

Fixed support of hidden content for Twitter Bootstrap 4.


### 1.1 (2017-12-02)

Support for PytSite-6.1.


### 1.0 (2017-11-25)

First release.
