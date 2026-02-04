"""
Unit Tests for Gold Fee Calculator

Tests the ENBD fee calculations against known values.
Uses gold_price=596 AED/gram and grams=1 as the validation benchmark.
"""

import pytest
from decimal import Decimal
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.fees.enbd import (
    ENBDFeeSchedule,
    calculate_scenario_1,
    calculate_scenario_2,
    calculate_enbd_scenario
)
from src.fees.dfm import (
    DFMFeeConfig,
    PaymentTiming,
    calculate_dfm_fees
)


class TestENBDFeeSchedule:
    """Test ENBD fee schedule constants."""
    
    def test_fee_schedule_values(self):
        """Verify fee schedule constants are correct."""
        schedule = ENBDFeeSchedule()
        
        assert schedule.acquisition_fee_per_gram == Decimal("0.1575")
        assert schedule.arrangement_fee_pct == Decimal("0.021")
        assert schedule.custody_fee_pct_years_1_5 == Decimal("0.00315")
        assert schedule.custody_fee_pct_years_6_plus == Decimal("0.0105")
        assert schedule.redemption_fee_pct == Decimal("0.00525")


class TestENBDScenario1:
    """Test ENBD Scenario 1: 5-year hold with 1 gram at 596 AED."""
    
    @pytest.fixture
    def scenario_1_result(self):
        """Calculate scenario 1 with benchmark values."""
        return calculate_scenario_1(gold_price_per_gram=596.0, grams=1)
    
    def test_gold_notional(self, scenario_1_result):
        """Test gold notional calculation."""
        assert float(scenario_1_result.gold_notional) == 596.0
    
    def test_acquisition_fee(self, scenario_1_result):
        """Test acquisition fee: 0.1575 per gram."""
        assert float(scenario_1_result.yearly_records[0].acquisition_fee) == 0.1575
    
    def test_arrangement_fee(self, scenario_1_result):
        """Test arrangement fee: 596 × 0.021 = 12.516."""
        expected = 596.0 * 0.021
        assert abs(float(scenario_1_result.yearly_records[0].arrangement_fee) - expected) < 0.0001
    
    def test_total_purchase_fees(self, scenario_1_result):
        """Test total purchase fees: 0.1575 + 12.516 = 12.6735."""
        expected = 0.1575 + (596.0 * 0.021)
        assert abs(float(scenario_1_result.total_purchase_fees) - expected) < 0.0001
    
    def test_custody_per_year(self, scenario_1_result):
        """Test custody per year (years 1-5): 596 × 0.00315 = 1.8774."""
        expected_custody = 596.0 * 0.00315
        
        # Check each holding year (years 1-4, before redemption year 5)
        for year in range(1, 5):
            record = scenario_1_result.yearly_records[year]
            assert abs(float(record.custody_accrual) - expected_custody) < 0.0001
    
    def test_total_custody(self, scenario_1_result):
        """Test total custody: 5 × 1.8774 = 9.387."""
        expected = 5 * (596.0 * 0.00315)
        assert abs(float(scenario_1_result.total_custody_paid) - expected) < 0.0001
    
    def test_redemption_fee(self, scenario_1_result):
        """Test redemption fee: 596 × 0.00525 = 3.129."""
        expected = 596.0 * 0.00525
        assert abs(float(scenario_1_result.redemption_fee) - expected) < 0.0001
    
    def test_total_fees_scenario_1(self, scenario_1_result):
        """
        Test total fees for Scenario 1:
        Purchase fees + Custody + Redemption
        = 12.6735 + 9.387 + 3.129 = 25.1895
        """
        expected = 0.1575 + (596.0 * 0.021) + (5 * 596.0 * 0.00315) + (596.0 * 0.00525)
        assert abs(float(scenario_1_result.total_fees) - expected) < 0.001
        
        # Also check against the stated expected value
        assert abs(float(scenario_1_result.total_fees) - 25.1895) < 0.001
    
    def test_year_count(self, scenario_1_result):
        """Test that scenario 1 has 6 yearly records (year 0-5)."""
        assert len(scenario_1_result.yearly_records) == 6
    
    def test_redemption_year_event(self, scenario_1_result):
        """Test that year 5 is marked as redemption."""
        assert scenario_1_result.yearly_records[5].event == "Redeem"


class TestENBDScenario2:
    """Test ENBD Scenario 2: 10-year hold with 1 gram at 596 AED."""
    
    @pytest.fixture
    def scenario_2_result(self):
        """Calculate scenario 2 with benchmark values."""
        return calculate_scenario_2(gold_price_per_gram=596.0, grams=1)
    
    def test_gold_notional(self, scenario_2_result):
        """Test gold notional calculation."""
        assert float(scenario_2_result.gold_notional) == 596.0
    
    def test_custody_years_1_5(self, scenario_2_result):
        """Test custody for years 1-5: 596 × 0.00315 = 1.8774 per year."""
        expected = 596.0 * 0.00315
        
        for year in range(1, 6):
            record = scenario_2_result.yearly_records[year]
            assert abs(float(record.custody_accrual) - expected) < 0.0001
    
    def test_custody_years_6_10(self, scenario_2_result):
        """Test custody for years 6-10: 596 × 0.0105 = 6.258 per year."""
        expected = 596.0 * 0.0105
        
        for year in range(6, 11):
            record = scenario_2_result.yearly_records[year]
            assert abs(float(record.custody_accrual) - expected) < 0.0001
    
    def test_total_custody_scenario_2(self, scenario_2_result):
        """
        Test total custody for Scenario 2:
        Years 1-5: 5 × (596 × 0.00315) = 9.387
        Years 6-10: 5 × (596 × 0.0105) = 31.29
        Total: 40.677
        """
        custody_1_5 = 5 * (596.0 * 0.00315)
        custody_6_10 = 5 * (596.0 * 0.0105)
        expected_total = custody_1_5 + custody_6_10
        
        assert abs(float(scenario_2_result.total_custody_paid) - expected_total) < 0.001
    
    def test_total_fees_scenario_2(self, scenario_2_result):
        """
        Test total fees for Scenario 2:
        Purchase: 0.1575 + 12.516 = 12.6735
        Custody: 9.387 + 31.29 = 40.677
        Redemption: 3.129
        Total: 56.4795
        """
        purchase = 0.1575 + (596.0 * 0.021)
        custody = (5 * 596.0 * 0.00315) + (5 * 596.0 * 0.0105)
        redemption = 596.0 * 0.00525
        expected = purchase + custody + redemption
        
        assert abs(float(scenario_2_result.total_fees) - expected) < 0.001
    
    def test_year_count(self, scenario_2_result):
        """Test that scenario 2 has 11 yearly records (year 0-10)."""
        assert len(scenario_2_result.yearly_records) == 11


class TestENBDMultipleGrams:
    """Test ENBD calculations with multiple grams."""
    
    def test_scenario_1_10_grams(self):
        """Test scenario 1 with 10 grams - fees should scale linearly."""
        result_1g = calculate_scenario_1(596.0, 1)
        result_10g = calculate_scenario_1(596.0, 10)
        
        # Total fees should scale by 10x
        assert abs(float(result_10g.total_fees) - 10 * float(result_1g.total_fees)) < 0.01
    
    def test_scenario_1_100_grams(self):
        """Test scenario 1 with 100 grams."""
        result = calculate_scenario_1(596.0, 100)
        
        expected_notional = 596.0 * 100  # 59,600
        assert float(result.gold_notional) == expected_notional
        
        # Acquisition should be 100 × 0.1575 = 15.75
        assert abs(float(result.yearly_records[0].acquisition_fee) - 15.75) < 0.01


class TestDFMCalculations:
    """Test DFM configurable fee calculations."""
    
    def test_dfm_zero_fees(self):
        """Test DFM with all zero fees."""
        config = DFMFeeConfig()  # All defaults are 0
        result = calculate_dfm_fees(596.0, 1, 5, config)
        
        assert float(result.total_fees) == 0.0
    
    def test_dfm_match_enbd(self):
        """Test DFM matching ENBD rates for 5-year hold."""
        config = DFMFeeConfig.from_enbd_rates()
        dfm_result = calculate_dfm_fees(596.0, 1, 5, config)
        enbd_result = calculate_scenario_1(596.0, 1)
        
        # Results should be very close
        assert abs(float(dfm_result.total_fees) - float(enbd_result.total_fees)) < 0.01
    
    def test_dfm_annual_custody_payment(self):
        """Test DFM with annual custody payment timing."""
        config = DFMFeeConfig(
            custody_fee_pct=Decimal("0.00315"),
            custody_timing=PaymentTiming.ANNUAL
        )
        result = calculate_dfm_fees(596.0, 1, 5, config)
        
        # Custody should be paid each year, not just at redemption
        for year in range(1, 5):
            record = result.yearly_records[year]
            assert float(record.custody_paid) > 0
    
    def test_dfm_holding_period_1_year(self):
        """Test DFM with 1-year holding period."""
        config = DFMFeeConfig(
            purchase_fee_per_gram=Decimal("0.1575"),
            custody_fee_pct=Decimal("0.00315"),
            redemption_fee_pct=Decimal("0.00525")
        )
        result = calculate_dfm_fees(596.0, 1, 1, config)
        
        assert len(result.yearly_records) == 2  # Year 0 (purchase) and Year 1 (redeem)
        assert result.yearly_records[0].event == "Purchase"
        assert result.yearly_records[1].event == "Redeem"


class TestFeePercentages:
    """Test fee percentage calculations."""
    
    def test_scenario_1_fee_percentage(self):
        """Test total fees as percentage of notional for Scenario 1."""
        result = calculate_scenario_1(596.0, 1)
        
        # 25.1895 / 596 ≈ 4.226%
        expected_pct = 25.1895 / 596.0
        assert abs(float(result.total_fees_pct) - expected_pct) < 0.001
    
    def test_scenario_2_fee_percentage(self):
        """Test total fees as percentage of notional for Scenario 2."""
        result = calculate_scenario_2(596.0, 1)
        
        # Higher percentage due to longer hold and higher custody rate
        assert float(result.total_fees_pct) > float(calculate_scenario_1(596.0, 1).total_fees_pct)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
