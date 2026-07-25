class VoiceDependencyMissing(RuntimeError):
    """
    Raised when a voice component is used but its optional dependency
    (I-11, `pip install -r requirements-voice.txt`) isn't installed.
    Distinct from a plain ImportError so API code can catch exactly
    this and turn it into an actionable 503, not an opaque 500.
    """
