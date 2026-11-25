from collections.abc import Sequence  # noqa: F401
from datetime import date
from decimal import Decimal

import pytest

from pricing.candidates import Candidate
from pricing.estimation import (
    calculate_mean,
    calculate_median,
    calculate_min,
    get_calculation_prices,
    requires_justification,
)


def _CandidateStub(
    awarded_unit_price: Decimal | None = None,
    estimated_unit_price: Decimal | None = None,
    secret_budget: bool = False,
) -> Candidate:
    return Candidate(
        id=1,
        description="Candidato sintético",
        unit="unidade",
        quantity=Decimal("1"),
        agency="Órgão fictício",
        date=date(2026, 1, 1),
        awarded_unit_price=awarded_unit_price,
        estimated_unit_price=estimated_unit_price,
        secret_budget=secret_budget,
    )


class TestCalculationFunctionsCaput:
    """Tests for estimation methods under Art. 6 caput of IN 65/2021."""

    def test_art6_caput_mean_computes_arithmetic_mean(self):
        """Art. 6 caput: mean method computes arithmetic mean of prices."""
        prices = [Decimal("10.00"), Decimal("20.00"), Decimal("30.00")]
        result = calculate_mean(prices)
        assert result == Decimal("20.00")
        assert isinstance(result, Decimal)

    def test_art6_caput_mean_handles_unsorted_input(self):
        """Art. 6 caput: mean does not depend on input ordering."""
        prices_asc = [Decimal("10.50"), Decimal("20.00"), Decimal("35.50")]
        prices_scrambled = [Decimal("35.50"), Decimal("10.50"), Decimal("20.00")]
        assert calculate_mean(prices_asc) == calculate_mean(prices_scrambled)

    def test_art6_caput_median_odd_count(self):
        """Art. 6 caput: median of odd count is the middle value."""
        prices = [Decimal("10.00"), Decimal("25.00"), Decimal("50.00")]
        result = calculate_median(prices)
        assert result == Decimal("25.00")
        assert isinstance(result, Decimal)

    def test_art6_caput_median_odd_count_unsorted(self):
        """Art. 6 caput: median of unsorted input finds middle value correctly."""
        prices = [Decimal("50.00"), Decimal("10.00"), Decimal("25.00")]
        result = calculate_median(prices)
        assert result == Decimal("25.00")

    def test_median_even_count_is_mean_of_two_middle_values(self):
        """Statistical convention: median of even count is the mean of two middle values."""
        prices = [
            Decimal("10.00"),
            Decimal("20.00"),
            Decimal("30.00"),
            Decimal("40.00"),
        ]
        result = calculate_median(prices)
        assert result == Decimal("25.00")
        assert isinstance(result, Decimal)

    def test_median_even_count_unsorted_exact_decimal(self):
        """Contract (D14): median of even count unsorted without rounding."""
        prices = [
            Decimal("0.40"),
            Decimal("0.10"),
            Decimal("0.30"),
            Decimal("0.20"),
        ]
        result = calculate_median(prices)
        assert result == Decimal("0.25")
        assert isinstance(result, Decimal)

    def test_median_exact_unrounded_cents(self):
        """Contract (D14): median of two adjacent cent values produces exact half-cent."""
        prices = [Decimal("10.00"), Decimal("10.01")]
        result = calculate_median(prices)
        assert result == Decimal("10.005")
        assert isinstance(result, Decimal)

    def test_median_even_count_does_not_leak_through_float(self):
        """Contract (D14): median of 0.10 and 0.20 produces exact 0.15 without float leak."""
        prices = [Decimal("0.10"), Decimal("0.20")]
        result = calculate_median(prices)
        assert result == Decimal("0.15")
        assert isinstance(result, Decimal)

    def test_median_exact_fractional_scale_without_four_decimal_rounding(self):
        """Contract (D14): median at 4-decimal minimum scale produces exact 5-decimal result."""
        prices = [Decimal("0.0001"), Decimal("0.0002")]
        result = calculate_median(prices)
        assert result == Decimal("0.00015")
        assert isinstance(result, Decimal)

    def test_art6_caput_min_computes_lowest_value(self):
        """Art. 6 caput: lowest value method returns the minimum price."""
        prices = [Decimal("30.00"), Decimal("12.50"), Decimal("45.00")]
        result = calculate_min(prices)
        assert result == Decimal("12.50")
        assert isinstance(result, Decimal)

    def test_art6_caput_min_unsorted_input(self):
        """Art. 6 caput: lowest value correctly finds minimum regardless of position."""
        prices = [Decimal("99.90"), Decimal("15.00"), Decimal("25.00")]
        assert calculate_min(prices) == Decimal("15.00")

    def test_art6_caput_min_below_one_centavo(self):
        """Contract (D14): lowest value below one centavo preserves fractional scale."""
        prices = [Decimal("0.0004"), Decimal("0.0009")]
        result = calculate_min(prices)
        assert result == Decimal("0.0004")
        assert isinstance(result, Decimal)


class TestEstimatedValueEdgeCases:
    """Tests for boundary conditions: single price, two prices, empty list."""

    def test_single_price_mean_returns_same_price(self):
        """Single price: mean returns the price itself as Decimal."""
        prices = [Decimal("42.50")]
        result = calculate_mean(prices)
        assert result == Decimal("42.50")
        assert isinstance(result, Decimal)

    def test_single_price_median_returns_same_price(self):
        """Single price: median returns the price itself as Decimal."""
        prices = [Decimal("42.50")]
        result = calculate_median(prices)
        assert result == Decimal("42.50")
        assert isinstance(result, Decimal)

    def test_single_price_min_returns_same_price(self):
        """Single price: lowest value returns the price itself as Decimal."""
        prices = [Decimal("42.50")]
        result = calculate_min(prices)
        assert result == Decimal("42.50")
        assert isinstance(result, Decimal)

    def test_two_prices_mean_returns_exact_midpoint(self):
        """Two prices: mean returns exact midpoint."""
        prices = [Decimal("10.00"), Decimal("25.00")]
        assert calculate_mean(prices) == Decimal("17.50")

    def test_two_prices_median_returns_exact_midpoint(self):
        """Two prices: median is mean of the two middle values."""
        prices = [Decimal("10.00"), Decimal("25.00")]
        assert calculate_median(prices) == Decimal("17.50")

    def test_two_prices_min_returns_lowest(self):
        """Two prices: lowest value returns minimum."""
        prices = [Decimal("25.00"), Decimal("10.00")]
        assert calculate_min(prices) == Decimal("10.00")

    def test_empty_prices_mean_raises_value_error(self):
        """Empty list: mean raises ValueError; estimated value is never zero."""
        with pytest.raises(ValueError, match="At least one price is required"):
            calculate_mean([])

    def test_empty_prices_median_raises_value_error(self):
        """Empty list: median raises ValueError; estimated value is never zero."""
        with pytest.raises(ValueError, match="At least one price is required"):
            calculate_median([])

    def test_empty_prices_min_raises_value_error(self):
        """Empty list: lowest value raises ValueError; estimated value is never zero."""
        with pytest.raises(ValueError, match="At least one price is required"):
            calculate_min([])


class TestRequiresJustificationParagraph5:
    """Tests for justification predicate under Art. 6, § 5 of IN 65/2021 (RN06)."""

    def test_art6_paragraph5_requires_justification_with_zero_prices(self):
        """Art. 6 § 5 (RN06): 0 prices is fewer than 3, requires justification."""
        assert requires_justification([]) is True

    def test_art6_paragraph5_requires_justification_with_one_price(self):
        """Art. 6 § 5 (RN06): 1 price is fewer than 3, requires justification."""
        prices = [Decimal("100.00")]
        assert requires_justification(prices) is True

    def test_art6_paragraph5_requires_justification_with_two_prices(self):
        """Art. 6 § 5 (RN06): 2 prices is fewer than 3, requires justification."""
        prices = [Decimal("100.00"), Decimal("105.00")]
        assert requires_justification(prices) is True

    def test_art6_caput_does_not_require_justification_with_three_prices(self):
        """Art. 6 caput: 3 prices meets the regulatory minimum; no justification required."""
        prices = [Decimal("98.00"), Decimal("100.00"), Decimal("102.00")]
        assert requires_justification(prices) is False

    def test_art6_caput_does_not_require_justification_with_more_than_three_prices(self):
        """Art. 6 caput: more than 3 prices; no justification required."""
        prices = [
            Decimal("95.00"),
            Decimal("98.00"),
            Decimal("100.00"),
            Decimal("102.00"),
        ]
        assert requires_justification(prices) is False


class TestGetCalculationPrices:
    """Tests for get_calculation_prices query method under Rafael's decision 1."""

    def test_get_calculation_prices_returns_awarded_prices_only(self):
        c1 = _CandidateStub(awarded_unit_price=Decimal("15.50"))
        c2 = _CandidateStub(awarded_unit_price=Decimal("20.00"))
        assert get_calculation_prices([c1, c2]) == [Decimal("15.50"), Decimal("20.00")]

    def test_get_calculation_prices_excludes_estimated_prices(self):
        c_awarded = _CandidateStub(awarded_unit_price=Decimal("15.50"))
        c_estimated = _CandidateStub(awarded_unit_price=None, estimated_unit_price=Decimal("18.00"))
        assert get_calculation_prices([c_awarded, c_estimated]) == [Decimal("15.50")]

    def test_get_calculation_prices_excludes_secret_budget(self):
        c_secret = _CandidateStub(
            awarded_unit_price=None,
            estimated_unit_price=Decimal("0.00"),
            secret_budget=True,
        )
        assert get_calculation_prices([c_secret]) == []

    def test_get_calculation_prices_excludes_zero_or_negative_prices(self):
        c_zero = _CandidateStub(awarded_unit_price=Decimal("0.00"))
        c_neg = _CandidateStub(awarded_unit_price=Decimal("-5.00"))
        assert get_calculation_prices([c_zero, c_neg]) == []

    def test_zero_or_estimated_prices_never_reach_calculation_functions(self):
        candidates = [
            _CandidateStub(awarded_unit_price=Decimal("10.00")),
            _CandidateStub(awarded_unit_price=Decimal("20.00")),
            _CandidateStub(awarded_unit_price=Decimal("30.00")),
            _CandidateStub(awarded_unit_price=None, estimated_unit_price=Decimal("999.00")),
            _CandidateStub(
                awarded_unit_price=None,
                estimated_unit_price=Decimal("0.00"),
                secret_budget=True,
            ),
            _CandidateStub(awarded_unit_price=Decimal("0.00")),
        ]
        prices = get_calculation_prices(candidates)
        assert prices == [Decimal("10.00"), Decimal("20.00"), Decimal("30.00")]
        assert calculate_mean(prices) == Decimal("20.00")
        assert calculate_median(prices) == Decimal("20.00")
        assert calculate_min(prices) == Decimal("10.00")

    def test_get_calculation_prices_rejects_non_candidate_objects(self):
        """N2: Only Candidate instances may contribute a calculation price."""

        class DuckCandidate:
            price = Decimal("99.00")

        class DuckCandidateWithPriceContract:
            usable_calculation_price = Decimal("88.00")

        with pytest.raises(TypeError, match="Candidate"):
            get_calculation_prices([DuckCandidate()])

        with pytest.raises(TypeError, match="Candidate"):
            get_calculation_prices([DuckCandidateWithPriceContract()])

        with pytest.raises(TypeError, match="Candidate"):
            get_calculation_prices([Decimal("50.00")])
