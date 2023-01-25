import collections
from .common import is_dict, is_numeric

NEG_PFX = '~'  # Prefix to indicate negation of a method
NOARGS_SFX = '()'  # Suffix to indicate that method takes no arguments
DEFAULT_ACTION_KEY = None
preprocessing_keys = {'series.lower', 'patterns.lower'}


_default_settings = {
    DEFAULT_ACTION_KEY: 'eq',
    'NAType': 'isna()',  # pattern is pd.NA
    'set': 'isin',
    'function': 'apply',
    'str': {'str.contains': {'case': True, 'regex': False}}
}


class Settings(collections.UserDict):
    def __init__(self, data=None, **kwargs):
        self.actions = {}
        if data is None:
            data = _default_settings
        super().__init__(data, **kwargs)

    def copy(self):  # TODO: check for the need of deep copy
        self_copy = Settings({})
        self_copy.update(self.data)
        return self_copy

    def update(self, data, **kwargs):
        super().update(data, **kwargs)
        self._update_actions()

    def _update_actions(self):
        for key, value in self.items():
            if key not in preprocessing_keys:
                self.actions[key] = _parse_action(value)

    def get_action(self, spec=None, pattern=None):
        _default = self.actions.get(DEFAULT_ACTION_KEY)
        if spec is None:  # by pattern class name
            action = self.actions.get(pattern.__class__.__name__, _default)
        elif is_numeric(spec):
            action = self.actions.get(spec, _default)
        else:
            action = _parse_action(spec)
        return action


def _parse_action(action):
    base, method, kwargs, negate, noargs = None, None, None, None, None
    if is_dict(action):
        for method, kwargs in action.items():
            break
    else:
        method = action
    if isinstance(method, str) and method:
        # Detect negate instruction
        if method.startswith(NEG_PFX):
            negate = True
            method = method[len(NEG_PFX):]
        if method.endswith(NOARGS_SFX):
            method = method[:-len(NOARGS_SFX)]
            noargs = True
        # Separate base and method
        *base, method = method.strip().strip('.').split('.')
        base = '.'.join(base)
    if base:
        result = {'base': base, 'method': method}
    else:
        result = {'method': method}
    if negate:
        result['negate'] = True
    if noargs:
        result['noargs'] = True
    if kwargs:
        result['kwargs'] = kwargs
    return result
