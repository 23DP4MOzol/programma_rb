from __future__ import annotations

import unittest

from serial_parsing import extract_preferred_serial, normalize_for_store


class SerialParsingTests(unittest.TestCase):
    def test_scanner_prefixed_token(self) -> None:
        token = extract_preferred_serial("S18167522504743", mode="scanner")
        self.assertEqual(token, "S18167522504743")
        self.assertEqual(normalize_for_store(token), "18167522504743")

    def test_scanner_plain_13_digits_supported(self) -> None:
        token = extract_preferred_serial("1811522502833", mode="scanner")
        self.assertEqual(token, "1811522502833")
        self.assertEqual(normalize_for_store(token), "1811522502833")

    def test_laptop_qr_uses_first_token(self) -> None:
        token = extract_preferred_serial("5CG3285C9K,6V5X8AV,1y1y0y", mode="scanner")
        self.assertEqual(token, "5CG3285C9K")
        self.assertEqual(normalize_for_store(token), "5CG3285C9K")

    def test_scanner_token_wins_inside_mixed_payload(self) -> None:
        token = extract_preferred_serial("ABC12345,S24022524205201,ZZ", mode="scanner")
        self.assertEqual(token, "S24022524205201")

    def test_reject_space_separated_non_laptop_tokens_in_scanner_mode(self) -> None:
        token = extract_preferred_serial("5CG3285C9K 6V5X8AV", mode="scanner")
        self.assertIsNone(token)

    def test_accept_generic_single_token_in_laptop_mode(self) -> None:
        token = extract_preferred_serial("5CG21582B1", mode="laptop")
        self.assertEqual(token, "5CG21582B1")

    def test_laptop_qr_first_token_with_semicolon_payload(self) -> None:
        token = extract_preferred_serial("5CG3285C9K;HP EliteBook 840 G10;RIMI001", mode="scanner")
        self.assertEqual(token, "5CG3285C9K")
        self.assertEqual(normalize_for_store(token), "5CG3285C9K")


if __name__ == "__main__":
    unittest.main()
