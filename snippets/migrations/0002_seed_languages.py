from django.db import migrations


LANGUAGES = [
    ('Python', 'python', 'python'),
    ('Django', 'django', 'django'),
    ('JavaScript', 'javascript', 'javascript'),
    ('HTML', 'html', 'html'),
    ('CSS', 'css', 'css'),
    ('C++', 'cpp', 'cpp'),
    ('SQL', 'sql', 'sql'),
    ('Bash', 'bash', 'bash'),
]


def seed_languages(apps, schema_editor):
    Language = apps.get_model('snippets', 'Language')
    # Historical models used inside RunPython don't run the real save()
    # override, so the slug must be supplied explicitly here.
    for name, slug, lexer in LANGUAGES:
        Language.objects.get_or_create(name=name, defaults={'slug': slug, 'pygments_lexer': lexer})


def unseed_languages(apps, schema_editor):
    Language = apps.get_model('snippets', 'Language')
    Language.objects.filter(name__in=[n for n, _, _ in LANGUAGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('snippets', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_languages, unseed_languages),
    ]
