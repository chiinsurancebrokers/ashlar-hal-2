from backend.app.providers.service import provider_definition, _host_allowed

def test_morgan_price_registry():
    p=provider_definition("morgan_price")
    assert p["name"] == "Morgan Price (Europe) ApS"
    assert "morgan-price.eu" in p["allowed_hosts"]
    assert any(s["kind"]=="about" for s in p["sources"])

def test_provider_allowlist():
    assert _host_allowed("morgan-price.eu", ["morgan-price.eu"])
    assert not _host_allowed("example.com", ["morgan-price.eu"])
