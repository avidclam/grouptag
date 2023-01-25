import numpy as np
import scipy
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.utils.validation import check_is_fitted
from .ruleframe import get_ruleframe_vectors

OOVW_TRY_LIMIT = 1000
OOVW_LEN = 5

_vectorizer_default_kwargs = {
    'analyzer': 'word',
    'strip_accents': 'unicode',
    'ngram_range': (1, 3),
    'lowercase': True,
    'binary': True
}


class VectorTagger:
    def __init__(self, **kwargs):
        _vectorizer_kwargs = _vectorizer_default_kwargs.copy()
        _vectorizer_kwargs.update(kwargs)
        self.vectorizer = CountVectorizer(**_vectorizer_kwargs)
        self.doc_term = None
        self.corpus_index = None

    def fit(self, corpus):
        self.corpus_index = corpus.index
        self.doc_term = self.vectorizer.fit_transform(corpus)
        return self

    def transform(self, ruleframe):
        check_is_fitted(self.vectorizer)
        _vectors = get_ruleframe_vectors(ruleframe, self.get_oov_word())
        tag, phrase, add_on_phrase, nullifier, min_terms = _vectors
        tag_resolver = np.r_[pd.NA, tag]
        phrase_term = self.vectorizer.transform(phrase)
        if add_on_phrase is not None:
            phrase_term -= self.vectorizer.transform(add_on_phrase)
        doc_phrase = self.doc_term.dot(phrase_term.transpose())
        if min_terms is not None:
            d_min_terms = scipy.sparse.diags(min_terms - 1, dtype=int)
            doc_phrase -= doc_phrase.sign().dot(d_min_terms)
            doc_phrase.data.clip(0, out=doc_phrase.data)
            doc_phrase.eliminate_zeros()
        if nullifier is not None:
            nullifier_term = self.vectorizer.transform(nullifier)
            doc_nullifier = self.doc_term.dot(nullifier_term.transpose())
            null_mark = doc_phrase.sign().multiply(doc_nullifier.sign())
            doc_phrase -= doc_phrase.multiply(null_mark)
        tag_idx = np.array(doc_phrase.argmax(axis=1).flat)
        na_shift = np.sign(doc_phrase.sum(axis=1).flat)
        doc_tag = tag_resolver[tag_idx + na_shift]
        return pd.Series(doc_tag, index=self.corpus_index)

    def get_oov_word(self):
        lower_abc = list('abcdefghijklmnopqrstuvwxyz')
        for _ in range(OOVW_TRY_LIMIT):
            randomword = ''.join(np.random.choice(lower_abc, size=OOVW_LEN))
            if randomword not in self.vectorizer.vocabulary_:
                break
        else:  # Just in case: almost unreal to reach
            raise RuntimeError("Can't generate out-of-vocabulary word.")
        return randomword


