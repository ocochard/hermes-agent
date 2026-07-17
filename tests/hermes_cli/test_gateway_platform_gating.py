"""Host-specific gating in ``hermes_cli.gateway._all_platforms()``.

Some messaging platforms can't function on every host. The gate lives
in one place — ``_all_platforms()`` — so the setup wizard, the curses
gateway-config menu, and any future picker all see the same filtered
list.

Currently:
- Matrix is hidden on Windows. The ``[matrix]`` extra pulls
  ``mautrix[encryption]`` -> ``python-olm``, which has no Windows wheel
  and needs ``make`` + libolm to build from sdist. There's no native
  Windows path that works.
"""

import pytest

class TestMatrixHiddenOnWindows:

    @pytest.mark.platforms("windows")
    def test_matrix_absent_on_windows(self):
        """The gate itself: matrix must be dropped on a real Windows host.

        A patched ``sys.platform`` proved only that the ``if`` branch runs;
        on native Windows this also proves the picker the user actually sees
        omits the platform whose dependency cannot build here.
        """
        import hermes_cli.gateway as gateway_mod

        platforms = gateway_mod._all_platforms()
        keys = {p["key"] for p in platforms}
        assert "matrix" not in keys, "matrix must be hidden on Windows"


class TestFreebsdRcPresentOnFreebsd:
    """The service-manager detectors are mutually exclusive on each host.
    On FreeBSD, ``supports_freebsd_rc`` picks up the port-installed rc.d
    script; no other manager reports available."""

    def _stub_env(self, monkeypatch, platform):
        """Neutralize the file-existence + PATH sniffs so the detector's
        platform check is the only variable."""
        import hermes_cli.gateway as gateway_mod
        import hermes_cli.gateway_freebsd as freebsd_mod
        from pathlib import Path

        monkeypatch.setattr(gateway_mod.sys, "platform", platform)
        monkeypatch.setattr(freebsd_mod.sys, "platform", platform)
        # Every escalator + rc.d + service(8) sniff returns "present"
        monkeypatch.setattr(gateway_mod.shutil, "which", lambda name: f"/x/{name}")
        monkeypatch.setattr(freebsd_mod.shutil, "which", lambda name: f"/x/{name}")
        monkeypatch.setattr(Path, "exists", lambda self: True)
        # Systemd operational probe would otherwise shell out; short-circuit.
        monkeypatch.setattr(gateway_mod, "_wsl_systemd_operational", lambda: True)
        monkeypatch.setattr(gateway_mod, "_systemd_operational", lambda system=False: True)
        # is_freebsd, is_termux, is_wsl, is_container all delegate to
        # sys.platform / env; freeze them on the FreeBSD detector's
        # dependencies.
        monkeypatch.setattr(gateway_mod, "is_termux", lambda: False)
        monkeypatch.setattr(gateway_mod, "is_wsl", lambda: False)
        monkeypatch.setattr(gateway_mod, "is_container", lambda: False)
        monkeypatch.setattr(freebsd_mod, "_freebsd_is_root", lambda: True)

    def test_freebsd_rc_detected_on_freebsd(self, monkeypatch):
        import hermes_cli.gateway as gateway_mod
        self._stub_env(monkeypatch, "freebsd16")
        assert gateway_mod.supports_freebsd_rc() is True

    def test_freebsd_rc_absent_on_linux(self, monkeypatch):
        import hermes_cli.gateway as gateway_mod
        self._stub_env(monkeypatch, "linux")
        assert gateway_mod.supports_freebsd_rc() is False

    def test_freebsd_rc_absent_on_macos(self, monkeypatch):
        import hermes_cli.gateway as gateway_mod
        self._stub_env(monkeypatch, "darwin")
        assert gateway_mod.supports_freebsd_rc() is False

    def test_freebsd_rc_absent_on_windows(self, monkeypatch):
        import hermes_cli.gateway as gateway_mod
        self._stub_env(monkeypatch, "win32")
        assert gateway_mod.supports_freebsd_rc() is False

    def test_service_managers_mutually_exclusive_on_freebsd(self, monkeypatch):
        # On FreeBSD, freebsd_rc claims the host and neither systemd nor
        # macOS/Windows detectors fire.
        import hermes_cli.gateway as gateway_mod
        self._stub_env(monkeypatch, "freebsd16")
        assert gateway_mod.supports_freebsd_rc() is True
        assert gateway_mod.supports_systemd_services() is False
        assert gateway_mod.is_macos() is False
        assert gateway_mod.is_windows() is False
