"""PytSite Form Plugin Controllers
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import routing as _routing
from . import _api


class Submit(_routing.Controller):
    def exec(self):
        frm = _api.dispense(self.request, self.args.pop('__form_uid'))

        # Setup widgets for all steps
        for step in range(1, frm.steps + 1):
            frm.current_step = step
            frm.setup_widgets()

        # Fill, validate and submit
        return frm.fill(self.args).validate().submit()
