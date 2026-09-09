from pathlib import Path

HTML=(Path(__file__).resolve().parents[1]/"frontend"/"index.html").read_text(encoding="utf-8")

def test_single_interface_host_exists():
    assert 'id="stableAdviser"' in HTML
    assert "body.adviser-active .shell.adviser-shell" in HTML

def test_activate_adviser_does_not_hide_welcome():
    block=HTML.split("function activateAdviser(){",1)[1].split("function showWelcome(){",1)[0]
    assert ".classList.add('hidden')" not in block
    assert "stableChatHost" in block

def test_microphone_is_toggle():
    assert "function toggleRecording()" in HTML
    assert "mediaRecorder.state==='recording'" in HTML
    assert "stopRecording();" in HTML
    assert "tap again to stop and transcribe" in HTML

def test_stream_cleanup_exists():
    assert "function cleanupRecordingStream()" in HTML
    assert "getTracks().forEach" in HTML

def test_inline_favicon_avoids_404():
    assert 'rel="icon"' in HTML
    assert 'href="/favicon.ico"' not in HTML
