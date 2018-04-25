"""PytSite Form API
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import util as _util, cache as _cache, logger as _logger
from . import _form


def dispense(uid: str) -> _form.Form:
    """Dispense a form
    """
    try:
        cid = uid.replace('cid:', '') if uid.startswith('cid:') else _cache.get_pool('form.form_cid').get(uid)

        cls =_util.get_module_attr(cid)
        if not issubclass(cls, _form.Form):
            raise RuntimeError('Unexpected form class')

        return cls(_uid=uid)

    except _cache.error.KeyNotExist:
        raise RuntimeError('Invalid form UID')

    # Hide all other exceptions info from outer world
    except Exception as e:
        _logger.error(e)
        raise RuntimeError('Unexpected form exception')
