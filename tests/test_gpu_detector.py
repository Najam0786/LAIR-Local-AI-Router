from unittest.mock import MagicMock, patch

from app.hardware.gpu_detector import (
    detect_apple_unified_memory,
    detect_nvidia_vram_gb,
)


def test_detect_apple_unified_memory_true_on_arm_darwin():
    with patch("platform.system", return_value="Darwin"), patch(
        "platform.machine", return_value="arm64"
    ):
        assert detect_apple_unified_memory() is True


def test_detect_apple_unified_memory_false_on_intel_mac():
    with patch("platform.system", return_value="Darwin"), patch(
        "platform.machine", return_value="x86_64"
    ):
        assert detect_apple_unified_memory() is False


def test_detect_apple_unified_memory_false_on_windows():
    with patch("platform.system", return_value="Windows"), patch(
        "platform.machine", return_value="AMD64"
    ):
        assert detect_apple_unified_memory() is False


def test_detect_nvidia_vram_parses_csv_output():
    result = MagicMock(returncode=0, stdout="24576\n")

    with patch("subprocess.run", return_value=result):
        vram_gb = detect_nvidia_vram_gb()

    assert vram_gb == 24.0


def test_detect_nvidia_vram_returns_none_on_nonzero_exit():
    result = MagicMock(returncode=1, stdout="")

    with patch("subprocess.run", return_value=result):
        assert detect_nvidia_vram_gb() is None


def test_detect_nvidia_vram_returns_none_when_binary_missing():
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        assert detect_nvidia_vram_gb() is None


def test_detect_nvidia_vram_returns_none_on_unparseable_output():
    result = MagicMock(returncode=0, stdout="not a number\n")

    with patch("subprocess.run", return_value=result):
        assert detect_nvidia_vram_gb() is None
