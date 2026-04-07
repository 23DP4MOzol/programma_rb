from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseSmokeTests(unittest.TestCase):
    def test_web_index_has_release_controls(self) -> None:
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        required_ids = [
            'id="syncNow"',
            'id="exportCsv"',
            'id="auditCard"',
            'id="authInfo"',
            'id="scanPopup"',
            'id="scanPopupRegister"',
        ]
        for marker in required_ids:
            self.assertIn(marker, html)

    def test_web_app_has_auth_and_conflict_guards(self) -> None:
        js = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")
        required_markers = [
            "AUTH_TOKEN_STORAGE_KEY",
            "resolveAuthContext",
            "applyAuthUiState",
            "expected_updated_at",
            "processQueuedSaves",
            "loadAuditLogs",
            "const firstSpace = text.indexOf(\" \")",
            "showScanPopup",
            "registerPendingDevice",
        ]
        for marker in required_markers:
            self.assertIn(marker, js)
        self.assertNotIn('split(" ", 2)', js)

        db_lookup_pos = js.find("device = await getDeviceBySerial(cleaned)")
        learned_guess_pos = js.find("const guessed = guessFromCache(cleaned)")
        self.assertGreaterEqual(db_lookup_pos, 0)
        self.assertGreaterEqual(learned_guess_pos, 0)
        self.assertLess(db_lookup_pos, learned_guess_pos)

    def test_desktop_app_has_role_controls(self) -> None:
        py = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        required_markers = [
            "def _refresh_auth_claims(self)",
            "def _apply_role_controls(self)",
            "Admin role required for audit viewer",
            "def _schedule_scanner_focus_lock(self)",
            "def _show_scan_result_popup(self",
            "Register new device",
        ]
        for marker in required_markers:
            self.assertIn(marker, py)

    def test_release_workflows_exist(self) -> None:
        workflows = ROOT / ".github" / "workflows"
        self.assertTrue((workflows / "release_e2e_smoke.yml").exists())
        self.assertTrue((workflows / "build_webview_apk_production.yml").exists())

        production_text = (workflows / "build_webview_apk_production.yml").read_text(encoding="utf-8")
        self.assertIn("rollout_track", production_text)
        self.assertIn("stable", production_text)
        self.assertIn("test", production_text)

    def test_backup_runbook_exists(self) -> None:
        self.assertTrue((ROOT / "BACKUP_RECOVERY_RUNBOOK.md").exists())


if __name__ == "__main__":
    unittest.main()
