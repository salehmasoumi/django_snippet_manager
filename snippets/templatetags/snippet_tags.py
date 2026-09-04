from django import template
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

register = template.Library()


@register.filter(name='highlight_code')
def highlight_code(snippet):
    """Server-side syntax highlighting via Pygments (initial render).
    Prism.js (loaded in base.html) re-highlights client-side and powers
    the copy-code interactivity, per the hybrid approach we agreed on."""
    code = snippet.code if hasattr(snippet, 'code') else snippet
    lexer_alias = getattr(getattr(snippet, 'language', None), 'pygments_lexer', None)
    try:
        lexer = get_lexer_by_name(lexer_alias) if lexer_alias else guess_lexer(code)
    except ClassNotFound:
        lexer = guess_lexer(code)
    formatter = HtmlFormatter(nowrap=True)
    return mark_safe(highlight(code, lexer, formatter))


@register.simple_tag
def total_public_snippets():
    from snippets.models import Snippet
    return Snippet.objects.filter(visibility=Snippet.Visibility.PUBLIC).count()
