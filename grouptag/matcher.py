import pandas as pd
from .common import is_dict, is_list, is_and_logic
from .explain import explain


def get_matcher(spec, level, settings):
    is_group, _spec, _level = _search_nested(spec, level)
    if is_group:
        matcher = GroupMatcher(_spec, _level, settings)
    else:
        matcher = AtomicMatcher(_spec, _level, settings)
    return matcher


def _search_nested(spec, level):
    is_group, _spec, _level = False, spec, level
    if (is_dict(spec) or is_list(spec)) and len(spec) > 1:
        is_group = True
    elif is_list(spec) and len(spec) == 1:
        is_group, _spec, _level = _search_nested(spec[0], level + 1)
    return is_group, _spec, _level


@explain
class GroupMatcher:
    def __init__(self, spec, level, settings):
        self.spec = spec
        self.level = level
        self.settings = settings
        self.matchers = []
        assert (is_list(self.spec) or is_dict(self.spec)) and self.spec
        if is_dict(self.spec):
            _spec_group = ({k: v} for k, v in self.spec.items())
        else:
            _spec_group = self.spec
        for spec in _spec_group:
            matcher = get_matcher(spec, self.level + 1, self.settings)
            self.matchers.append(matcher)

    def __call__(self, series):
        if is_and_logic(self.level):
            mask = pd.Series(True, index=series.index)
            for matcher in self.matchers:
                mask &= matcher(series)
        else:
            mask = pd.Series(False, index=series.index)
            for matcher in self.matchers:
                mask |= matcher(series)
        return mask


@explain
class AtomicMatcher:
    def __init__(self, spec, level, settings):
        self.spec = spec
        self.level = level
        self.settings = settings

    def __call__(self, series):
        pattern, action = self._parse_atomic_spec(self.spec)
        assert 'error' in action or 'method' in action
        if 'error' in action:
            raise ValueError(action['error'])
        if 'base' in action:
            method_base = getattr(series, action['base'])
        else:
            method_base = series
        method_callable = getattr(method_base, action['method'])
        if action.get('noargs', False):
            match = method_callable()
        else:
            method_kwargs = action.get('kwargs', {})
            match = method_callable(pattern, **method_kwargs)
        negate = action.get('negate', False)
        return (~match).fillna(False) if negate else match.fillna(False)

    def _parse_atomic_spec(self, spec):
        # Parses pattern-action specification and checks for validity
        pattern, action_spec = None, None
        if is_dict(spec) and spec:
            for pattern, action_spec in spec.items():
                break
        else:
            pattern, action_spec = spec, None
        # Need to lowercase the pattern?
        if self.settings.get('patterns.lower', False):
            pattern = get_lower_pattern(pattern)
        action = self.settings.get_action(action_spec, pattern)
        if is_dict(action):
            action = _check_action(action)
        else:
            action = {'error': 'Missing action', 'action spec': action_spec}
        return pattern, action


def get_lower_pattern(pattern):
    if isinstance(pattern, str):
        result = pattern.lower()
    elif isinstance(pattern, (list, tuple, set)):
        result = pattern.__class__(get_lower_pattern(ptn) for ptn in pattern)
    else:
        result = pattern
    return result


def _check_action(action):
    assert is_dict(action)
    # Check action method
    err_msg = None
    if 'method' in action:
        base, method = action.get('base', None), action['method']
        method_callable = method
        method_callable_str = str(method)
        if isinstance(method, str):
            method_base = pd.Series
            method_base_str = 'Series'
            # Check if base is valid
            if base:
                if hasattr(method_base, base):
                    method_base = getattr(pd.Series, base)
                    method_base_str = f'Series.{base}'
                else:
                    err_msg = f"Series has no attribute '{base}'"
            # Check if method is valid
            if not err_msg and hasattr(method_base, method):
                method_callable = getattr(method_base, method)
            else:
                err_msg = f"{method_base_str} has no method '{method}'"
            method_callable_str = f"{method_base_str}.{method}"
        # Check if method is callable
        if not (err_msg or callable(method_callable)):
            err_msg = f"Method '{method_callable_str}' is not callable"
    else:
        err_msg = 'No method specified.'
    # Check kwargs
    suppress_kwargs = True
    if 'kwargs' in action:
        kwargs = action['kwargs']
        if kwargs:
            suppress_kwargs = False
            if not is_dict(kwargs):
                err_msg = "Method's kwargs invalid, args not supported"
    # Get the results right
    result = {} if not err_msg else {'error': err_msg}
    for key in ('negate', 'noargs', 'base', 'method'):
        if key in action:
            result[key] = action[key]
    if not suppress_kwargs:
        result['kwargs'] = action['kwargs']
    return result
