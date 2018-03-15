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

        self.args.add_formatter('step', _formatters.AboveZeroInt())

    def exec(self) -> list:
        frm = _api.dispense(self.args.pop('uid'))
        frm.current_step = self.args.pop('step')

        r = []
        for w in frm.setup_widgets().get_widgets():
            # Return only top-level widgets, because they render their children's HTML code by themselves
            if not w.parent:
                r.append(w.render())

        return r


class PostValidate(_routing.Controller):
    """Default form's AJAX validator
    """

    def __init__(self):
        super().__init__()

        self.args.add_formatter('step', _formatters.AboveZeroInt())

    def exec(self) -> dict:
        try:
            frm = _api.dispense(self.args.pop('uid'))
            frm.current_step = self.args.pop('step')
            frm.setup_widgets().fill(self.args).validate()

            return {'status': True}

        except _error.ValidationError as e:
            return {'status': False, 'messages': e.errors}
