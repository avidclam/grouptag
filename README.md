# Grouptag, categorization by rules
Grouptag is a Python package aimed at pattern- or keyword-based categorization (tagging) of text records.
It's a companion to proven technologies: pattern part relies on the capabilities of Pandas Series, while keyword search is based on CountVectorizer from scikit-learn.
## Use Case Example
Author of the package often uses it when a column in a dataset is _almost_ categorical, but needs to be cleaned from extra symbols and alternative spelling before any practical "group by" aggregation might happen.

Here's an example. Suppose you've got the results of a simple survey — "Which beer is the best for you?" — and the task is to rank beer brands by popularity. 

Among many others, you'd like to distinguish between Budweiser and Bud Light brands of Anheuser-Busch (AB InBev). 
The values in the survey results include 'Budweiser', 'Bud', 'Bud!', 'Bud Lite', 'Bud Light' and many other variations. 
Industry expert has suggested that all records that contain 'Budweiser' or 'Bud' (without 'Lite' or "Light') should be tagged (grouped into) 'Budweiser', while the ones that contain 'Lite' or "Light' in addition to 'Budweiser' or 'Bud' should be tagged 'Bud Light'.
## Solutions with Grouptag
Let's imitate this case.
```python
import pandas as pd
from grouptag import quicktag, whichtag, VectorTagger

survey = pd.Series(['Bud!', 'Bud Light', 'Bud Lite', 'Bud', 'Budweiser'])
```

### Quicktag, easy dialect
```python
quicktag_rules = {    
    'Bud Light': [['Bud', ['Lite', 'Light']]],  # 'Bud' AND ('Lite' OR 'Light')    
    'Budweiser': 'Bud'  # Everything that contains 'bud'
}
survey_df = pd.DataFrame({
    'raw_answer': survey,
    'group_tag': quicktag(survey, quicktag_rules)
})
```
The result — `survey_df` — is according to the rules:

|   | raw_answer | group_tag |
|---|------------|-----------|
| 0 | Bud!       | Budweiser |
| 1 | Bud Light  | Bud Light |
| 2 | Bud Lite   | Bud Light |
| 3 | Bud        | Budweiser |
| 4 | Budweiser  | Budweiser |

Quicktag rules come in a form of a `{'tag': <group of patters>}` dictionary. 

Binary logic may accompany patterns in a group:
- `['Pattern 1', 'Pattern 2']` means ('Pattern 1' OR 'Pattern 2')
- `[['Pattern 1', 'Pattern 2']]` means ('Pattern 1' AND 'Pattern 2')
- `['Pattern 1', ['Pattern 2', 'Pattern 3']]` means 'Pattern 1' OR ('Pattern 2' AND 'Pattern 3')
- `[['Pattern 1', ['Pattern 2', 'Pattern 3']]]` means 'Pattern 1' AND ('Pattern 2' OR 'Pattern 3')

You see, binary logic is inverted with every nested level down.

The rules are processed in order. 
If one rule worked on a particular value, the others are not checked. 
When designing the ruleset, make sure more specific rules go first, before the generic ones.

### Whichtag, more control
The other function for the pattern-matching activities is `whichtag`. 
It uses a more complex syntax for greater flexibility and performance. 
The rest of the usage is the same.

The rules for the example would look like this:
```python
whichtag_rules = [
    {
        # Change settings anywhere along the ruleset, as often as needed
        'str': {'str.contains': {'case': True, 'regex': False}},  # see below
        'series.lower': True,
        'patterns.lower': True
    },
    ['Bud Light', 'Bud', ['Lite', 'Light']],  # Top-level logic is 'AND'
    ['Budweiser', 'Bud']
]
```
Explanation to the settings above:
 
String `'str': {'str.contains': {'case': True, 'regex': False}}` means:
 
>For a series of 'str' type use `str.contains` method of pandas series with the named parameters `case` and `regex` that follow next.

There's a reason why `'case': True`. 
Settings `'series.lower': True` and `'patterns.lower': True` perform lowercase transformation of both series and patterns _before_ rules are being checked, `str.contains` method doesn't have to repeat it within each rule. 
This behaviour of `str.contains` is achieved with `'case': True`. 
By the way, this parameter is set by default and can be omitted altogether.

> **_NOTE:_**  One has to be very careful with `'patterns.lower'` setting when using regular expressions since they are case-sensitive.

### VectorTagger, keyword search approach
This class presents alternative, keyword-based approach to tagging.
```python
ruleframe = pd.DataFrame({
    'tag': ['Bud Light', 'Bud Light', 'Budweiser'],
    'phrase': ['Bud Light Lite', 'Budweiser Light Lite', 'Bud Budweiser'],
    'min_terms': [2, 2, 1]
})
tagger = VectorTagger()
tagger = tagger.fit(survey)
survey_df = pd.DataFrame({
    'raw_answer': survey,
    'group_tag': tagger.transform(ruleframe)
})
# This result is the same as above
```
Here one can't rely on patterns (e.g. 'bud' matching 'budweiser' being its substring), every word needs to be explicit in the ruleset. 

Important for the tagger's distinguishing ability is the `min_terms` parameter. 
It tells the tagger, for example, to match the lines that contain _at least two_ words from the 'Bud Light Lite' phrase. 
In case of 'Bug Budweiser' any word will do since `min_terms=1`.
> Technically, implementation is a bit more complicated. 
> Vectorizer splits a series into n-grams. 
> For example, 'bud' and 'bud light' will count as separate terms. 
> This allows to take into account the order of adjacent words.

Order or rules is important in VectorTagger: the rule that matches first, tags first!

VectorTagger has an advantage over the pattern-based approach. 
Tagger might take considerable time to vectorize the series — `tagger.fit()` — on a large dataset, 
but subsequent application of ruleframes runs relatively fast. 
Instant feedback is very important when ruleframe is being designed. 
Also, ruleframe is a table (author uses Excel to edit ruleframes) with simple logic 
which is quite easy to explain to a subject-matter expert. 
This allows data analysis teams to split efforts between technical and expert tasks.