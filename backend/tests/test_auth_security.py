from backend.rnw.services.auth_service import password_strength_errors


def test_password_strength_requires_complexity():
    errors = password_strength_errors("password")
    assert any("uppercase" in item for item in errors)
    assert any("number" in item for item in errors)
    assert any("symbol" in item for item in errors)


def test_password_strength_accepts_complex_password():
    assert password_strength_errors("StrongPass123!") == []
