import pandas as pd
from .common import is_dict, is_list
from .settings import Settings
from .matcher import get_matcher
from .tagged import TaggedSeries
from .explain import explain

# Join logic for the group of top-level pattern masks is 'AND'
TOP_LEVEL = 0


def quicktag(series, rules, prefill=pd.NA, case=False, regex=False):
    settings = {'series.lower': not case,
                # regex patterns are case-sensitive and should not be lowercased
                'patterns.lower': not (case or regex),
                'str': {'str.contains': {'case': True, 'regex': regex}}}
    spec = [settings]
    spec.extend(gen_from_quicktag(rules))
    return whichtag(series, spec, prefill=prefill)


def whichtag(series, rules, prefill=pd.NA):
    tagger = PatternTagger(rules)
    tagged_series = tagger(series, prefill)
    return tagged_series.tag


def gen_from_quicktag(spec):
    assert is_dict(spec)
    for tag, lop in spec.items():  # lop: list of patterns
        if is_list(lop) and len(lop) == 1 and is_list(lop[0]):
            yield [tag, *lop[0]]  # [[...]] opens as ...
        else:
            yield [tag, lop]


@explain
class PatternTagger:
    def __init__(self, rules):
        self.log = {}
        self.rules_spec = rules
        self.rule_chain = []
        # Set chain of Rules
        settings = Settings()
        for rule_spec in self.rules_spec:
            if is_dict(rule_spec):
                settings.update(rule_spec)
            else:
                self.rule_chain.append(Rule(rule_spec, settings))

    def __call__(self, series, prefill):
        # TODO: Fix the case of non-unique index
        tagged_series = TaggedSeries(series, prefill)
        for rule in self.rule_chain:
            if tagged_series.untagged_index.empty:
                break
            tagged_series = rule(tagged_series)
        self.log['series.size'] = series.size
        self.log['tagged'] = tagged_series.tagged_index.size
        self.log['untagged'] = tagged_series.untagged_index.size
        return tagged_series


@explain
class Rule:
    def __init__(self, rule_spec, settings):
        self.log = {'reached': False}
        self.rule_spec = rule_spec
        self.settings = settings.copy()
        # Assign matcher
        if is_list(self.rule_spec):
            self.tag, *gopas = rule_spec  # Group of Pattern Action Specifiers
        else:  # short for 'tag equals pattern'
            self.tag, gopas = self.rule_spec, [self.rule_spec]
        self.matcher = get_matcher(gopas, TOP_LEVEL, self.settings)

    def __call__(self, tagged_series: TaggedSeries):
        self.log = {'reached': True}
        lower_setting = self.settings.get('series.lower', False)
        untagged = tagged_series.use_lowercase(lower_setting).untagged
        mask = self.matcher(untagged)
        assert mask.size == tagged_series.untagged_index.size
        num_matched = mask.sum()
        self.log['matched'] = num_matched
        if num_matched:
            tagged_series[mask] = self.tag
        return tagged_series
