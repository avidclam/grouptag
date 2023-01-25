"""
Pattern- or keyword-based categorization (tagging) of text records.
"""

__title__ = __name__
__description__ = __doc__.replace('\n', ' ').replace('\r', '').strip()
__version__ = '0.1'
__author__ = 'Aleksandr Mikhailov'
__author_email__ = 'dev@avidclam.com'
__copyright__ = '2023, Aleksandr Mikhailov'


from .whichtag import whichtag, quicktag, PatternTagger
from .vectortagger import VectorTagger
from .ruleframe import fix_ruleframe
__all__ = ['whichtag', 'quicktag',
           'PatternTagger', 'VectorTagger', 'fix_ruleframe']
