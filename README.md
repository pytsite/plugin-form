# PytSite Form Plugin


## Changelog


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
