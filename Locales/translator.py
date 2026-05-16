from Locales.ru import TEXTS as ru
from Locales.en import TEXTS as en

LANGS = {
    "ru": ru,
    "en": en,
}


def t(lang: str, key: str, **kwargs):
    text = LANGS.get(lang, en).get(key, key)
    return text.format(**kwargs)