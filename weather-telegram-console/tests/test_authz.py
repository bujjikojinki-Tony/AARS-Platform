from weather_telegram_console.authz import Authz


def test_authz_admin():
    authz = Authz(admin_user_ids={123}, admin_usernames={"polyaarstempbot"})
    assert authz.is_admin(123) is True
    assert authz.is_admin(999) is False
    assert authz.is_admin(None, "PolyAARSTempbot") is True
