import unittest

from check_bom_stock import BomPart, StockPart, check_parts


def stock(
    *,
    row: int = 2,
    value: str = "100n",
    lcsc: str = "C14663",
    symbol: str = "Device:C_Small",
    footprint: str = "Capacitor_SMD:C_0603_1608Metric",
    quantity: float = 100,
    datasheet: str = "https://www.lcsc.com/datasheet/C14663.pdf",
) -> StockPart:
    return StockPart(row, value, lcsc, symbol, footprint, quantity, datasheet)


def bom(
    *,
    references: tuple[str, ...] = ("C1", "C2"),
    value: str = "100n",
    lcsc: str = "C14663",
    symbol: str = "Device:C_Small",
    footprint: str = "Capacitor_SMD:C_0603_1608Metric",
    datasheet: str = "https://www.lcsc.com/datasheet/C14663.pdf",
) -> BomPart:
    return BomPart(references, value, lcsc, symbol, footprint, datasheet)


class CheckBomStockTests(unittest.TestCase):
    def test_matching_part_passes(self):
        self.assertEqual(check_parts([bom()], [stock()], 20), [])

    def test_blank_lcsc_is_an_error_but_na_uses_value(self):
        errors = check_parts([bom(lcsc="")], [stock()], 20)
        self.assertIn("LCSC Part # is not assigned", errors[0])
        self.assertEqual(check_parts([bom(lcsc="N/A")], [stock()], 20), [])

    def test_value_must_exist_even_when_lcsc_is_na(self):
        errors = check_parts([bom(value="missing", lcsc="N/A")], [stock()], 20)
        self.assertIn("does not exist", errors[0])

    def test_reports_value_metadata_and_stock_mismatches(self):
        errors = check_parts(
            [bom(value="10u", footprint="wrong", datasheet="wrong")],
            [stock(value="100n", quantity=19)],
            20,
        )
        self.assertEqual(len(errors), 5)
        self.assertTrue(any("value '10u'" in error for error in errors))
        self.assertTrue(any("does not match workbook row" in error for error in errors))
        self.assertTrue(any("footprint" in error for error in errors))
        self.assertTrue(any("datasheet" in error for error in errors))
        self.assertTrue(any("minimum is 20" in error for error in errors))

    def test_na_rejects_ambiguous_same_value_rows(self):
        errors = check_parts(
            [bom(lcsc="N/A")],
            [stock(row=2), stock(row=3, lcsc="C999")],
            20,
        )
        self.assertIn("ambiguous", errors[0])


if __name__ == "__main__":
    unittest.main()
