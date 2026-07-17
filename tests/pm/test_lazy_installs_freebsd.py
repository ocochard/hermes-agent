"""Platform default for security.allow_lazy_installs.

FreeBSD's misc/hermes-agent port installs into a pkg(8)-owned tree, so the
runtime fallback must be off there; an explicit config value still wins.
"""

import sys

import pytest

import hermes_cli.config as config_mod
from pm.install import lazy_installs_allowed


@pytest.fixture
def config(monkeypatch):
    """Point the gate at an in-memory config and clear the env override."""
    monkeypatch.delenv("HERMES_DISABLE_LAZY_INSTALLS", raising=False)
    monkeypatch.setattr(config_mod, "require_readable_config_before_write", lambda: None)
    holder = {"cfg": {"security": {}}}
    monkeypatch.setattr(config_mod, "load_config_readonly", lambda: holder["cfg"])
    return holder


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_default_enabled_off_freebsd(config, monkeypatch, platform):
    monkeypatch.setattr(sys, "platform", platform)
    assert lazy_installs_allowed() is True


def test_default_disabled_on_freebsd(config, monkeypatch):
    monkeypatch.setattr(sys, "platform", "freebsd16")
    assert lazy_installs_allowed() is False


def test_explicit_opt_in_on_freebsd(config, monkeypatch):
    monkeypatch.setattr(sys, "platform", "freebsd16")
    config["cfg"] = {"security": {"allow_lazy_installs": True}}
    assert lazy_installs_allowed() is True


def test_explicit_opt_out_on_linux(config, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    config["cfg"] = {"security": {"allow_lazy_installs": False}}
    assert lazy_installs_allowed() is False


def test_template_default_follows_platform():
    from hermes_cli.config_defaults import DEFAULT_CONFIG

    expected = not sys.platform.startswith("freebsd")
    assert DEFAULT_CONFIG["security"]["allow_lazy_installs"] is expected
