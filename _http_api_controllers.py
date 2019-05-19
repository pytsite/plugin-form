"""PytSite Form Plugin HTTP API Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import routing as _routing, formatters as _formatters
from . import _error, _api, _form


def _setup_form_widgets(frm: _form.Form, step: int):
    frm.current_step = step
    frm.setup_widgets()

    # Check for duplicates
    uids = []
    for w in frm.get_widgets():
        if w.uid in uids:
            raise RuntimeError("Widget '{}' is duplicated on form '{}'".format(w.uid, frm.name))
        uids.append(w.uid)

    return frm


class PostGetWidgets(_routing.Controller):
    """Get widgets of the form for particular step

    POST method is used here due to large request size in some cases.
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('__form_step', _formatters.AboveZeroInt())

    def exec(self) -> list:
        frm = _api.dispense(self.request, self.args.pop('__form_uid'))
        frm.name = self.args.pop('__form_name')

        return [str(w) for w in _setup_form_widgets(frm, self.args.pop('__form_step')).get_widgets()]


class PostValidate(_routing.Controller):
    """Default form's
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('__form_step', _formatters.AboveZeroInt())

    def exec(self) -> dict:
        try:
            frm = _api.dispense(self.request, self.args.pop('__form_uid'))
            frm.name = self.args.pop('__form_name')
            _setup_form_widgets(frm, self.args.pop('__form_step')).fill(self.args).validate()

            return {'status': True}

        except (_error.FormFillError, _error.FormValidationError) as e:
            return {'status': False, 'messages': e.errors}


class PostSubmit(_routing.Controller):
    def exec(self):
        frm = _api.dispense(self.request, self.args.pop('__form_uid'))

        # Setup widgets for all steps
        for step in range(1, frm.steps + 1):
            _setup_form_widgets(frm, step)

        # Fill, validate and submit
        r = frm.fill(self.args).validate().submit()

        if r is None and not frm.redirect:
            frm.redirect = self.request.referrer

        return {'__redirect': frm.redirect} if frm.redirect else r
