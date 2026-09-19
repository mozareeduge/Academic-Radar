from decimal import Decimal
import pytest

from academic_radar.domain.funding import (
    FundingInputs,
    FundingResult,
    compute_gap,
    fully_funded_label_allowed,
    assert_same_currency,
)


class TestExactDecimalArithmetic:
    def test_decimal_addition_exact(self):
        """Test exact Decimal arithmetic, not float approximation."""
        award = Decimal('0.10')
        fee_waiver = Decimal('0.20')
        result = award + fee_waiver
        assert result == Decimal('0.30')
        assert isinstance(result, Decimal)

    def test_compute_gap_exact_surplus(self):
        """Test exact Decimal gap computation with surplus."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('25000'),
            fee_waiver=Decimal('5000'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('2000'),
            living_costs=Decimal('10000'),
            insurance_visa_relocation=Decimal('1000'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        # (25000 + 5000 + 0) - (12000 + 2000 + 10000 + 1000) = 30000 - 25000 = 5000
        assert result.annual_gap_or_surplus == Decimal('5000')
        assert result.complete is True
        assert isinstance(result.annual_gap_or_surplus, Decimal)

    def test_compute_gap_exact_deficit(self):
        """Test exact Decimal gap computation with deficit."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('10000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('3000'),
            living_costs=Decimal('10000'),
            insurance_visa_relocation=Decimal('2000'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        # (10000 + 0 + 0) - (12000 + 3000 + 10000 + 2000) = 10000 - 27000 = -17000
        assert result.annual_gap_or_surplus == Decimal('-17000')
        assert result.complete is True
        assert isinstance(result.annual_gap_or_surplus, Decimal)


class TestUnknownHandling:
    def test_unknown_living_cost_blocks_gap(self):
        """Test that unknown living cost makes gap None and marks incomplete."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('20000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('10000'),
            mandatory_fees=Decimal('1000'),
            living_costs=None,  # Unknown
            insurance_visa_relocation=Decimal('500'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        assert result.annual_gap_or_surplus is None
        assert result.complete is False
        assert 'living_costs' in result.unknown_items

    def test_unknown_cost_items_blocks_complete(self):
        """Test that unknown cost items prevent complete status."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('25000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('10000'),
            mandatory_fees=Decimal('1000'),
            living_costs=Decimal('8000'),
            insurance_visa_relocation=Decimal('500'),
            duration_months=12,
            unknown_cost_items=['health insurance', 'transportation'],
        )
        result = compute_gap(inputs)
        assert result.complete is False
        assert 'health insurance' in result.unknown_items
        assert 'transportation' in result.unknown_items

    def test_multiple_unknowns_tracked(self):
        """Test that multiple unknown amounts are all tracked."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=None,  # Unknown
            fee_waiver=Decimal('0'),
            reliable_external=None,  # Unknown
            tuition=Decimal('10000'),
            mandatory_fees=Decimal('1000'),
            living_costs=Decimal('8000'),
            insurance_visa_relocation=Decimal('500'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        assert result.annual_gap_or_surplus is None
        assert result.complete is False
        assert 'annual_award' in result.unknown_items
        assert 'reliable_external' in result.unknown_items


class TestFullyFundedLabel:
    def test_fully_funded_gap_zero_complete(self):
        """Test fully funded label allowed when complete and gap == 0."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('25000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('2000'),
            living_costs=Decimal('10000'),
            insurance_visa_relocation=Decimal('1000'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        assert result.annual_gap_or_surplus == Decimal('0')
        assert result.complete is True
        assert fully_funded_label_allowed(result) is True

    def test_fully_funded_positive_gap_complete(self):
        """Test fully funded label allowed when complete and gap > 0."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('30000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('2000'),
            living_costs=Decimal('10000'),
            insurance_visa_relocation=Decimal('1000'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        assert result.annual_gap_or_surplus == Decimal('5000')
        assert result.complete is True
        assert fully_funded_label_allowed(result) is True

    def test_label_not_allowed_negative_gap(self):
        """Test fully funded label NOT allowed when gap < 0."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('15000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('2000'),
            living_costs=Decimal('10000'),
            insurance_visa_relocation=Decimal('1000'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        # (15000 + 0 + 0) - (12000 + 2000 + 10000 + 1000) = 15000 - 25000 = -10000
        assert result.annual_gap_or_surplus == Decimal('-10000')
        assert result.complete is True
        assert fully_funded_label_allowed(result) is False

    def test_label_not_allowed_incomplete(self):
        """Test fully funded label NOT allowed when incomplete."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('25000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('2000'),
            living_costs=None,  # Unknown
            insurance_visa_relocation=Decimal('1000'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        assert result.complete is False
        assert fully_funded_label_allowed(result) is False

    def test_label_not_allowed_with_unknown_cost_items(self):
        """Test fully funded label NOT allowed with unknown cost items."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('25000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('2000'),
            living_costs=Decimal('8000'),
            insurance_visa_relocation=Decimal('1000'),
            duration_months=12,
            unknown_cost_items=['health insurance'],
        )
        result = compute_gap(inputs)
        assert result.complete is False
        assert fully_funded_label_allowed(result) is False


class TestCurrencyConsistency:
    def test_same_currency_passes(self):
        """Test that same currency amounts pass validation."""
        assert_same_currency(
            Decimal('100'), Decimal('200'), Decimal('300'),
            currency='EUR'
        )

    def test_mixed_currencies_raise(self):
        """Test that mixed currencies raise ValueError."""
        with pytest.raises(ValueError, match='different currencies'):
            assert_same_currency(
                Decimal('100'), Decimal('200'),
                currencies=['EUR', 'GBP']
            )

    def test_none_amounts_allowed(self):
        """Test that None (unknown) amounts are allowed in consistency check."""
        assert_same_currency(
            Decimal('100'), None, Decimal('300'),
            currency='EUR'
        )


class TestDataTypes:
    def test_no_float_in_inputs(self):
        """Test that Decimal is used, not float."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('25000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('2000'),
            living_costs=Decimal('8000'),
            insurance_visa_relocation=Decimal('1000'),
            duration_months=12,
            unknown_cost_items=[],
        )
        assert isinstance(inputs.annual_award, Decimal)
        assert isinstance(inputs.tuition, Decimal)
        assert isinstance(inputs.living_costs, Decimal)

    def test_result_gap_is_decimal_not_float(self):
        """Test that result gap is Decimal, not float."""
        inputs = FundingInputs(
            currency='EUR',
            annual_award=Decimal('25000'),
            fee_waiver=Decimal('0'),
            reliable_external=Decimal('0'),
            tuition=Decimal('12000'),
            mandatory_fees=Decimal('2000'),
            living_costs=Decimal('8000'),
            insurance_visa_relocation=Decimal('1000'),
            duration_months=12,
            unknown_cost_items=[],
        )
        result = compute_gap(inputs)
        assert isinstance(result.annual_gap_or_surplus, Decimal)
        assert not isinstance(result.annual_gap_or_surplus, float)
