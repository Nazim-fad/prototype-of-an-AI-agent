from typing import Any, Dict, List, Optional

JSONDict = Dict[str, Any]


def _parse_number(s: str | None) -> Optional[float]:
    """Helper: turn '2,300.00' or '140.00' into float, or None."""
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def validate_invoice_math_tool(
    parsed_invoice: JSONDict,
    raw_text: str,
) -> JSONDict:
    """
    Name:
        validate_invoice_math

    Tool description:
        Check whether the arithmetic inside an invoice is consistent.

        It verifies:
        - for each line item: Qty * Unit Price ~= Line Total
        - that the sum of line totals ~= the Subtotal
        - that Subtotal + tax_amount ~= total_amount (from parsed_invoice)
        - and cross-checks any "Subtotal", "Sales Tax", and "Total Amount Due"
          rows in the markdown table.

    Input types and descriptions:
        parsed_invoice (dict):
            JSON-serializable representation of the parsed invoice, with
            numeric fields 'tax_amount' and 'total_amount' when available.
        raw_text (str):
            Full markdown/text representation of the invoice, including the
            items table.

    Output type:
        dict with the following keys:
            is_valid (bool or None):
                True if all checks pass, False if any inconsistency is found,
                or None if there was not enough information to perform checks.
            issues (list of str):
                Human-readable descriptions of any detected problems.
            subtotal (float or None):
                Subtotal inferred from the document (from table or text).
    """
    issues: List[str] = []
    line_items_ok = True

    # Parse the markdown table (rows starting with '|')
    lines = [l.rstrip() for l in raw_text.splitlines()]
    table_lines = [l.strip() for l in lines if l.strip().startswith("|")]

    line_totals: List[float] = []
    subtotal_row_amt: Optional[float] = None
    tax_row_amt: Optional[float] = None
    total_row_amt: Optional[float] = None

    # Skip header (first 2 rows: header + separator) if present
    data_rows = table_lines[2:] if len(table_lines) > 2 else table_lines

    for row in data_rows:
        # Remove leading/trailing '|' and split into cells
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 5:
            continue

        first_col = cells[0]
        qty_col = cells[2]
        unit_price_col = cells[3]
        line_total_col = cells[4]

        # Case 1: numeric item line (e.g. '1', '2', ...)
        if first_col.isdigit():
            qty = _parse_number(qty_col)
            unit_price = _parse_number(unit_price_col)
            line_total = _parse_number(line_total_col)

            if qty is None or unit_price is None or line_total is None:
                issues.append(
                    f"Could not parse numeric values for item row '{first_col}'."
                )
                line_items_ok = False
                continue

            expected = round(qty * unit_price, 2)
            line_totals.append(line_total)

            if abs(expected - line_total) > 0.01:
                line_items_ok = False
                issues.append(
                    f"Line item {first_col}: Qty * Unit Price = {expected:.2f} "
                    f"but Line Total is {line_total:.2f}."
                )

        # Case 2: subtotal / tax / total rows
        else:
            label = first_col.lower()
            amount = _parse_number(line_total_col)

            if "subtotal" in label:
                subtotal_row_amt = amount
            elif "tax" in label:
                tax_row_amt = amount
            elif "total amount due" in label or label.startswith("total"):
                total_row_amt = amount

    # Compute subtotal from line_totals if we have any
    subtotal_from_items: Optional[float] = None
    if line_totals:
        subtotal_from_items = round(sum(line_totals), 2)

    # Cross-check subtotal row
    if subtotal_from_items is not None and subtotal_row_amt is not None:
        if abs(subtotal_from_items - subtotal_row_amt) > 0.01:
            issues.append(
                "Subtotal mismatch: sum of line items = "
                f"{subtotal_from_items:.2f}, but Subtotal row = "
                f"{subtotal_row_amt:.2f}."
            )

    # Cross-check tax & total against parsed invoice values
    tax = parsed_invoice.get("tax_amount")
    total = parsed_invoice.get("total_amount")

    # If table tax row exists, compare with parsed tax
    if tax_row_amt is not None and tax is not None:
        if abs(tax_row_amt - tax) > 0.01:
            issues.append(
                f"Tax mismatch: table tax = {tax_row_amt:.2f}, "
                f"parsed tax_amount = {tax:.2f}."
            )

    # If table total row exists, compare with parsed total
    if total_row_amt is not None and total is not None:
        if abs(total_row_amt - total) > 0.01:
            issues.append(
                f"Total mismatch: table total = {total_row_amt:.2f}, "
                f"parsed total_amount = {total:.2f}."
            )

    # Check subtotal + tax ~= total, using best available numbers
    subtotal_for_check = (
        subtotal_row_amt
        if subtotal_row_amt is not None
        else subtotal_from_items
    )

    if subtotal_for_check is not None and tax is not None and total is not None:
        expected_total = round(subtotal_for_check + tax, 2)
        if abs(expected_total - total) > 0.01:
            issues.append(
                f"Subtotal + tax ({expected_total:.2f}) does not match "
                f"total_amount ({total:.2f})."
            )

    # Decide overall validity
    any_issues = len(issues) > 0

    # If we never parsed anything meaningful, return None
    if (
        subtotal_for_check is None
        and tax is None
        and total is None
        and not line_totals
    ):
        return {
            "is_valid": None,
            "issues": ["Not enough information to validate invoice math."],
            "subtotal": None,
        }

    is_valid_overall = (not any_issues) and line_items_ok

    return {
        "is_valid": is_valid_overall,
        "issues": issues,
        "subtotal": subtotal_for_check,
    }
