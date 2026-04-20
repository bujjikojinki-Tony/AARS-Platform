from weather_execution_gateway.risk.kill_switch import KillSwitch


def test_kill_switch():
    switch = KillSwitch(active=False)
    assert switch.is_active() is False
