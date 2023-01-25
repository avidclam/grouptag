import re
import pandas as pd


_ruleframe_column_patterns = {
    'tag': 'tag',
    'phrase': 'phrase',
    'min_terms': r'min_?terms?'
}


def get_ruleframe_vectors(ruleframe, oov_word):
    ruleframe_df = fix_ruleframe(ruleframe)
    try:
        _phrase = ruleframe_df['phrase']
        tag = ruleframe_df['tag']
    except KeyError:
        message = "Columns 'tag' and 'phrase' required in the rules frame."
        raise KeyError(message)
    min_terms = ruleframe_df.get('min_terms')
    if min_terms is not None and min_terms.eq(1).all():
        min_terms = None
    # Get ready with phrase, add_on_phrase, nullifier
    phrase, add_on_phrase, nullifier = [], [], []
    for line in _phrase:
        phrase_words, add_on_words, nullifier_words = [], [], []
        for word in line.split():
            if word.startswith('-'):
                nullifier_words.append(word[1:])
            elif word.startswith('+'):
                phrase_words.append(word[1:])
                add_on_words.append(word[1:])
            else:
                phrase_words.append(word)
                add_on_words.append(oov_word)
        phrase.append(' '.join(phrase_words))
        nullifier.append(' '.join(nullifier_words))
        add_on_phrase.append(' '.join(add_on_words))
    phrase = pd.Series(phrase, index=ruleframe_df.index)
    nullifier = pd.Series(nullifier, index=ruleframe_df.index)
    add_on_phrase = pd.Series(add_on_phrase, index=ruleframe_df.index)
    return (
        tag,
        phrase,
        add_on_phrase if add_on_phrase.str.len().sum() else None,
        nullifier if nullifier.str.len().sum() else None,
        min_terms
    )


def fix_ruleframe(ruleframe):
    if not isinstance(ruleframe, pd.DataFrame):
        raise TypeError('Ruleframe should be a pandas DataFrame')
    known_df, unknown_df = pd.DataFrame(), pd.DataFrame()
    for column_name, column in ruleframe.items():
        detected_name = column_name
        if isinstance(column_name, str):  # Detect by name
            for name, pattern in _ruleframe_column_patterns.items():
                if (re.match(pattern, column_name.lower()) and
                        name not in known_df.columns):
                    detected_name = name
                    break
        elif pd.api.types.is_numeric_dtype(column):  # Detect by type/ position
            if 'min_terms' not in known_df:
                detected_name = 'min_terms'
        else:
            for name in ('tag', 'phrase'):
                if name not in known_df:
                    detected_name = name
                    break
        if detected_name == 'tag':
            known_df['tag'] = column.fillna(method='ffill')
        elif detected_name == 'min_terms':
            known_df['min_terms'] = column.astype('UInt16').fillna(1).clip(1)
        elif detected_name == 'phrase':
            known_df[detected_name] = column
        else:
            unknown_df[detected_name] = column
    if unknown_df.empty:
        result_df = known_df
    else:
        result_df = pd.concat([known_df, unknown_df], axis=1)
    return result_df[~result_df['phrase'].isna()].copy()
