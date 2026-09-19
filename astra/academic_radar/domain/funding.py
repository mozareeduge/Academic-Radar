from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class FundingInputs:
    """All funding amounts must use Decimal, never float. Unknown amounts are None."""
    currency: str
    annual_award: Optional[Decimal]
    fee_waiver: Optional[Decimal]
    reliable_external: Optional[Decimal]
    tuition: Optional[Decimal]
    mandatory_fees: Optional[Decimal]
    living_costs: Optional[Decimal]
    insurance_visa_relocation: Optional[Decimal]
    duration_months: int
    unknown_cost_items: list[str] = field(default_factory=list)


@dataclass
class FundingResult:
    """Gap computation result with unknowns tracked."""
    annual_gap_or_surplus: Optional[Decimal]
    known_total_in: Decimal
    known_total_out: Decimal
    unknown_items: list[str]
    complete: bool


def assert_same_currency(*amounts, currency: Optional[str] = None, currencies: Optional[list[str]] = None):
    """Verify all amounts use the same currency. None (unknown) amounts are allowed."""
    if currencies and len(set(c for c in currencies if c is not None)) > 1:
        raise ValueError('Cannot add amounts in different currencies')


def compute_gap(inputs: FundingInputs) -> FundingResult:
    """
    Compute annual funding gap/surplus.

    Gap = (annual_award + fee_waiver + reliable_external)
        - (tuition + mandatory_fees + living_costs + insurance_visa_relocation)

    complete: True only if no required amount is None and unknown_cost_items is empty.
    annual_gap_or_surplus: None if any input amount needed is None (Unknown is not zero).
    """
    # Track unknown amounts needed for the formula
    unknown_items = []

    # Income side
    income_amounts = {
        'annual_award': inputs.annual_award,
        'fee_waiver': inputs.fee_waiver,
        'reliable_external': inputs.reliable_external,
    }

    # Expense side
    expense_amounts = {
        'tuition': inputs.tuition,
        'mandatory_fees': inputs.mandatory_fees,
        'living_costs': inputs.living_costs,
        'insurance_visa_relocation': inputs.insurance_visa_relocation,
    }

    # Collect all unknown amount items
    for key, value in {**income_amounts, **expense_amounts}.items():
        if value is None:
            unknown_items.append(key)

    # Calculate known totals (treating None as 0 for accounting purposes only)
    known_total_in = Decimal('0')
    for value in income_amounts.values():
        if value is not None:
            known_total_in += value

    known_total_out = Decimal('0')
    for value in expense_amounts.values():
        if value is not None:
            known_total_out += value

    # Determine completeness
    complete = len(unknown_items) == 0 and len(inputs.unknown_cost_items) == 0

    # Compute gap only if complete
    if complete:
        total_in = known_total_in
        total_out = known_total_out
        annual_gap_or_surplus = total_in - total_out
    else:
        annual_gap_or_surplus = None

    # Combine unknown tracking
    all_unknown_items = unknown_items + inputs.unknown_cost_items

    return FundingResult(
        annual_gap_or_surplus=annual_gap_or_surplus,
        known_total_in=known_total_in,
        known_total_out=known_total_out,
        unknown_items=all_unknown_items,
        complete=complete,
    )


def fully_funded_label_allowed(result: FundingResult) -> bool:
    """
    Label allowed only when:
    1. complete: True (no unknown amounts)
    2. annual_gap_or_surplus >= 0 (no deficit)
    """
    return result.complete and result.annual_gap_or_surplus is not None and result.annual_gap_or_surplus >= Decimal('0')
