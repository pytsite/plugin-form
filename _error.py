"""PytSite Form Plugin Errors
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class Error(Exception):
    pass


class FormFillError(Error):
    """Form Fill Error
    """

    def __init__(self, errors: dict):
        """Init
        """
        self._errors = errors

    @property
    def errors(self) -> dict:
        return self._errors


class FormValidationError(FormFillError):
    """Form Validation Error
    """
    pass


class WidgetNotExistError(Error):
    """Widget Not Exist Error
    """

    def __init__(self, uid: str):
        """Init
        """
        self._uid = uid

    def __str__(self):
        return "Widget '{}' does not exist".format(self._uid)
