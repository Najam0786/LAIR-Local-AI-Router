# Maps Whisper's ISO-639-1 detected-language codes to Kokoro's
# locale-tagged language codes (I-11). Kokoro's own supported set is
# much narrower than Whisper's; anything not listed here falls back to
# "en-us" rather than raising -- a reply in the wrong language is a
# real, honestly-accepted limitation of Kokoro's language coverage
# today, not a crash.
_WHISPER_TO_KOKORO = {
    "en": "en-us",
    "es": "es",
    "fr": "fr-fr",
    "hi": "hi",
    "it": "it",
    "pt": "pt-br",
    "ja": "ja",
    "zh": "zh",
}


def whisper_to_kokoro_lang(whisper_language_code: str | None) -> str:
    if not whisper_language_code:
        return "en-us"

    return _WHISPER_TO_KOKORO.get(whisper_language_code, "en-us")
