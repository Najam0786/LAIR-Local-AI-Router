from app.voice.language_map import whisper_to_kokoro_lang


def test_known_language_maps_to_kokoro_locale():
    assert whisper_to_kokoro_lang("en") == "en-us"
    assert whisper_to_kokoro_lang("fr") == "fr-fr"


def test_unknown_language_falls_back_to_en_us():
    assert whisper_to_kokoro_lang("xx") == "en-us"


def test_none_falls_back_to_en_us():
    assert whisper_to_kokoro_lang(None) == "en-us"
