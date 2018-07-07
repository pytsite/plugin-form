"""PytSite Form Plugin HTTP API Controllers
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import routing as _routing, formatters as _formatters
from . import _error, _api


class PostGetWidgets(_routing.Controller):
    """Get widgets of the form for particular step

    POST method is used here due to large request size in some cases.
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('__form_step', _formatters.AboveZeroInt())

    def exec(self) -> list:
        frm = _api.dispense(self.request, self.args.pop('__form_uid'))
        frm.current_step = self.args.pop('__form_step')
        frm.name =  self.args.pop('__form_name')

        return [str(w) for w in frm.setup_widgets().get_widgets()]


class PostValidate(_routing.Controller):
    """Default form's
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('__form_step', _formatters.AboveZeroInt())

    def exec(self) -> dict:
        try:
            frm = _api.dispense(self.request, self.args.pop('__form_uid'))
            frm.current_step = self.args.pop('__form_step')
            frm.name = self.args.pop('__form_name')
            frm.setup_widgets().fill(self.args).validate()

            return {'status': True}

        except _error.FormValidationError as e:
            return {'status': False, 'messages': e.errors}
