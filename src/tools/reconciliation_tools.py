from typing import Any, Dict, List, Optional
from smolagents import tool


JSONDict = Dict[str, Any]

@tool
def reconcile_invoice_with_db_tool(
    parsed_invoice: JSONDict,
    db_invoice: Optional[JSONDict],
) -> JSONDict:
    """
    Compare a parsed invoice with a stored invoice record in the database.

    Args:
        parsed_invoice: Parsed invoice fields from the uploaded document,
            typically containing at least 'total_amount' and 'tax_amount'.
        db_invoice: Invoice row fetched from the database, or None if no
            record was found for this invoice_id.

    Returns:
        A dictionary with:
            is_match: True if all compared numeric fields match within a
                small tolerance, False if any difference is detected, or
                None if there is no database record to compare.
            differences: List of human-readable messages describing any
                field-level mismatches (for example, differences in
                'total_amount' or 'tax_amount').
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
