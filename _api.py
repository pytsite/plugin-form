"""PytSite Form API
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import util as _util, cache as _cache, logger as _logger, http as _http
from . import _form


def dispense(request: _http.Request, uid: str) -> _form.Form:
    """Dispense a form
    """
    try:
        # Determine form's class
        cid = uid.replace('cid:', '') if uid.startswith('cid:') else _cache.get_pool('form.form_cid').get(uid)
        cls = _util.get_module_attr(cid)

        # Prevent instantiating other classes via HTTP API
        if not issubclass(cls, _form.Form):
            raise RuntimeError('Form class is not found')

        # Instantiate form
        return cls(request) if uid.startswith('cid:') else cls(request, _uid=uid)

    except _cache.error.KeyNotExist:
        raise RuntimeError('Invalid form UID')

    # Hide all other exceptions info from outer world
    except Exception as e:
        _logger.error(e)
        raise RuntimeError('Unexpected form exception')
