"""PytSite Form Plugin Controllers
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import routing as _routing
from . import _api


class Submit(_routing.Controller):
    def exec(self):
        args = dict(self.args)

        frm = _api.dispense(args)

        # Rebuild form
        if not frm.nocache:
            frm.remove_widgets()
            for step in range(1, frm.steps + 1):
                frm.step = step
                frm.setup_widgets(False)

        # Validate the form
        frm.fill(args, mode='validation').validate()

        # Refill the form in 'normal' mode
        frm.fill(args)

        # Notify form about submit
        return frm.submit()
