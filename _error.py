"""PytSite Form Plugin Errors
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class FormValidationError(Exception):
    """Validation Error Exception
    """

    def __init__(self, errors: dict):
        """Init
        """
        self._errors = errors

    @property
    def errors(self) -> dict:
        return self._errors


class WidgetNotExistError(Exception):
    def __init__(self, uid: str):
        """Init
        """
        self._uid = uid

    def __str__(self):
        return "Widget '{}' does not exist".format(self._uid)
