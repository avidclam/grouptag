from .common import is_dict, is_list, is_and_logic
from .settings import preprocessing_keys


def explain(cls):
    """Decorator that adds explain method if implemented."""
    explain_method = _explain_dispatcher.get(cls.__name__, explain_default)
    if callable(explain_method):
        setattr(cls, 'explain', explain_method)
    return cls


def explain_default(obj):
    name = obj.__class__.__name__
    err_msg = f"Explain method for class '{name}' is not implemented yet."
    return {'error': err_msg}


def explain_pattern_tagger(self):
    explanation = []
    active_settings_info = {}
    for rule in self.rule_chain:
        updated_settings = {}
        for key in preprocessing_keys & rule.settings.keys():
            value = rule.settings[key]
            if (
                    key not in active_settings_info or
                    active_settings_info[key] != value
            ):
                updated_settings[key] = value
        if updated_settings:
            explanation.append(updated_settings)
            active_settings_info.update(updated_settings)
        explanation.append(rule.explain())
    if self.log:
        explanation.append(self.log)
    return explanation


def explain_rule(self):
    explanation = {'tag': self.tag}
    explanation.update(self.log)
    matcher_explanation = self.matcher.explain()
    assert is_dict(matcher_explanation) or is_list(matcher_explanation)
    if is_dict(matcher_explanation):
        explanation.update(matcher_explanation)
    elif matcher_explanation:  # list with non-zero length
        target, *_ = matcher_explanation
        if is_dict(target):
            explanation.update(target)
            matcher_explanation[0] = explanation
            explanation = matcher_explanation
        else:
            matcher_explanation.insert(0, explanation)
            explanation = matcher_explanation
    return explanation


def explain_group_matcher(self):
    explained_logic = 'AND' if is_and_logic(self.level) else 'OR'
    explanation = [{'logic': explained_logic}]
    explanation.extend(matcher.explain() for matcher in self.matchers)
    return explanation


def explain_atomic_matcher(self):
    pattern, action = self._parse_atomic_spec(self.spec)
    explanation = {'pattern': pattern}
    explanation.update(action)
    return explanation


_explain_dispatcher = {
    'PatternTagger': explain_pattern_tagger,
    'Rule': explain_rule,
    'AtomicMatcher': explain_atomic_matcher,
    'GroupMatcher': explain_group_matcher
}
