from collections.abc import MutableSequence
import pandas as pd


class TaggedSeries:
    def __init__(self, series, prefill):
        self._use_lowercase = False
        self._cached_lower = None
        self._series = series
        self.untagged_index = self._series.index
        self.tagged_index = pd.Index([])
        if isinstance(prefill, pd.Series):
            self._series_tag = prefill.copy()
        else:
            self._series_tag = pd.Series(prefill, dtype='object',
                                         index=self.untagged_index)

    @property
    def series(self):
        if self._cached_lower is None and self._use_lowercase:
            self._cached_lower = self._series.str.lower()
        return self._cached_lower if self._use_lowercase else self._series

    @property
    def untagged(self):
        return self.series[self.untagged_index]

    @property
    def tag(self):
        return self._series_tag

    def use_lowercase(self, flag):
        self._use_lowercase = True if flag else False
        return self

    def __setitem__(self, key, value):
        # Only untagged items may be tagged.
        # Boolean key index should match the size of untagged index.
        if not isinstance(key, (MutableSequence, pd.Series, pd.Index)):
            key = [key]
        tag_idx = pd.Index(key)
        if tag_idx.is_boolean():
            tag_idx = self.untagged_index[tag_idx]
        if not tag_idx.empty:
            self._series_tag[tag_idx] = value
            self.tagged_index = self.tagged_index.union(tag_idx)
            self.untagged_index = self.untagged_index.difference(tag_idx)
