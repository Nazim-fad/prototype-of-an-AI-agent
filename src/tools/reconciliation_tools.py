# src/tools/reconciliation_tools.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

JSONDict = Dict[str, Any]


def reconcile_invoice_with_db_tool(
    parsed_invoice: JSONDict,
    db_invoice: Optional[JSONDict],
) -> JSONDict:
    """
    Name:
        reconcile_invoice_with_db

    Tool description:
        Compare key numeric fields in a parsed invoice with the
        corresponding values stored in the database.

    Input types and descriptions:
        parsed_invoice (dict):
            Parsed invoice as returned by parse_document, with fields such as
            'total_amount' and 'tax_amount'.
        db_invoice (dict or None):
            Existing invoice row from the database (via DBClient.get_invoice),
            or None if no record exists.

    Output type:
        dict with the following keys:
            is_match (bool or None):
                True if all compared fields match within tolerance,
                False if differences were found,
                or None if there was no DB record.
            differences (list of str):
                Human-readable descriptions of field-level differences, e.g.:
                "total_amount: db=4300.00, document=4376.78".
    """
    # No record to compare against
    if db_invoice is None:
        return {
            "is_match": None,
            "differences": ["No existing record found in the database."],
        }

    differences: List[str] = []

    # Compare selected numeric fields
    for field in ("total_amount", "tax_amount"):
        doc_val = parsed_invoice.get(field)
        db_val = db_invoice.get(field)
        if doc_val is None or db_val is None:
            continue

        if abs(float(doc_val) - float(db_val)) > 0.01:
            differences.append(
                f"{field}: db={float(db_val):.2f}, document={float(doc_val):.2f}"
            )

    is_match = len(differences) == 0

    return {
        "is_match": is_match,
        "differences": differences,
    }
