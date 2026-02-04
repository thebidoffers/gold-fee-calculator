"""
ENBD Gold Product Fee Calculator

This module implements the exact ENBD "Precious Metal – Gold" fee schedule
for benchmarking purposes.

Fee Schedule (Fixed Constants):
- Acquisition fee: AED 0.1575 per gram (one-time at purchase)
- Arrangement fee: 2.10% of gold notional (one-time at purchase)
- Custody & insurance fee:
  - 0.315% p.a. for years 1-5 (inclusive)
  - 1.05% p.a. for years 6+ (Scenario 2 only)
  - Accrues yearly, paid at redemption
- Redemption charge: 0.525% of notional (paid at redemption)
"""

from dataclasses import dataclass
from typing import List
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class ENBDFeeSchedule:
    """ENBD fee schedule constants."""
    acquisition_fee_per_gram: Decimal = Decimal("0.1575")
    arrangement_fee_pct: Decimal = Decimal("0.021")  # 2.1%
    custody_fee_pct_years_1_5: Decimal = Decimal("0.00315")  # 0.315% p.a.
    custody_fee_pct_years_6_plus: Decimal = Decimal("0.0105")  # 1.05% p.a.
    redemption_fee_pct: Decimal = Decimal("0.00525")  # 0.525%


@dataclass
class YearlyFeeRecord:
    """Represents fee breakdown for a single year."""
    year: int
    event: str
    gold_value: Decimal
    acquisition_fee: Decimal
    arrangement_fee: Decimal
    custody_accrual: Decimal
    redemption_fee: Decimal
    fees_paid: Decimal
    notes: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame creation."""
        return {
            "Year": self.year,
            "Event": self.event,
            "Gold Value (AED)": float(self.gold_value),
            "Acquisition Fee (AED)": float(self.acquisition_fee),
            "Arrangement Fee (AED)": float(self.arrangement_fee),
            "Custody Accrual (AED)": float(self.custody_accrual),
            "Redemption Fee (AED)": float(self.redemption_fee),
            "Fees Paid (AED)": float(self.fees_paid),
            "Notes": self.notes
        }


@dataclass
class ENBDScenarioResult:
    """Complete result for an ENBD scenario calculation."""
    scenario_name: str
    holding_years: int
    gold_price_per_gram: Decimal
    grams: int
    gold_notional: Decimal
    yearly_records: List[YearlyFeeRecord]
    total_purchase_fees: Decimal
    total_custody_paid: Decimal
    redemption_fee: Decimal
    total_fees: Decimal
    total_fees_pct: Decimal
    
    def get_summary(self) -> dict:
        """Get summary metrics as dictionary."""
        return {
            "Scenario": self.scenario_name,
            "Holding Period (Years)": self.holding_years,
            "Gold Price (AED/gram)": float(self.gold_price_per_gram),
            "Grams Purchased": self.grams,
            "Gold Notional (AED)": float(self.gold_notional),
            "Total Purchase Fees (AED)": float(self.total_purchase_fees),
            "Total Custody Paid (AED)": float(self.total_custody_paid),
            "Redemption Fee (AED)": float(self.redemption_fee),
            "Total Fees (AED)": float(self.total_fees),
            "Total Fees (% of Notional)": float(self.total_fees_pct * 100)
        }


def calculate_enbd_scenario(
    gold_price_per_gram: float,
    grams: int,
    holding_years: int,
    scenario_name: str
) -> ENBDScenarioResult:
    """
    Calculate ENBD gold product fees for a given scenario.
    
    Args:
        gold_price_per_gram: Gold price in AED per gram
        grams: Number of grams purchased
        holding_years: Number of years to hold (5 or 10)
        scenario_name: Name for the scenario (e.g., "Scenario 1: 5-Year Hold")
    
    Returns:
        ENBDScenarioResult with complete fee breakdown
    """
    # Convert to Decimal for precision
    price = Decimal(str(gold_price_per_gram))
    schedule = ENBDFeeSchedule()
    
    # Calculate gold notional
    gold_notional = price * grams
    
    # Calculate one-time purchase fees
    acquisition_fee = schedule.acquisition_fee_per_gram * grams
    arrangement_fee = gold_notional * schedule.arrangement_fee_pct
    total_purchase_fees = acquisition_fee + arrangement_fee
    
    # Calculate redemption fee
    redemption_fee = gold_notional * schedule.redemption_fee_pct
    
    # Build year-by-year records
    yearly_records = []
    custody_accruals = []
    
    for year in range(holding_years + 1):  # Year 0 to holding_years
        if year == 0:
            # Purchase year
            record = YearlyFeeRecord(
                year=0,
                event="Purchase",
                gold_value=gold_notional,
                acquisition_fee=acquisition_fee,
                arrangement_fee=arrangement_fee,
                custody_accrual=Decimal("0"),
                redemption_fee=Decimal("0"),
                fees_paid=total_purchase_fees,
                notes="One-time purchase fees paid"
            )
        elif year < holding_years:
            # Holding years (not final year)
            if year <= 5:
                custody_rate = schedule.custody_fee_pct_years_1_5
            else:
                custody_rate = schedule.custody_fee_pct_years_6_plus
            
            custody_accrual = gold_notional * custody_rate
            custody_accruals.append(custody_accrual)
            
            record = YearlyFeeRecord(
                year=year,
                event="Hold",
                gold_value=gold_notional,
                acquisition_fee=Decimal("0"),
                arrangement_fee=Decimal("0"),
                custody_accrual=custody_accrual,
                redemption_fee=Decimal("0"),
                fees_paid=Decimal("0"),
                notes=f"Custody accrues at {float(custody_rate)*100:.3f}%; charged upon redemption"
            )
        else:
            # Redemption year
            if year <= 5:
                custody_rate = schedule.custody_fee_pct_years_1_5
            else:
                custody_rate = schedule.custody_fee_pct_years_6_plus
            
            custody_accrual = gold_notional * custody_rate
            custody_accruals.append(custody_accrual)
            total_custody = sum(custody_accruals)
            
            record = YearlyFeeRecord(
                year=year,
                event="Redeem",
                gold_value=gold_notional,
                acquisition_fee=Decimal("0"),
                arrangement_fee=Decimal("0"),
                custody_accrual=custody_accrual,
                redemption_fee=redemption_fee,
                fees_paid=total_custody + redemption_fee,
                notes="All accrued custody + redemption fee paid"
            )
        
        yearly_records.append(record)
    
    # Calculate totals
    total_custody_paid = sum(custody_accruals)
    total_fees = total_purchase_fees + total_custody_paid + redemption_fee
    total_fees_pct = total_fees / gold_notional
    
    return ENBDScenarioResult(
        scenario_name=scenario_name,
        holding_years=holding_years,
        gold_price_per_gram=price,
        grams=grams,
        gold_notional=gold_notional,
        yearly_records=yearly_records,
        total_purchase_fees=total_purchase_fees,
        total_custody_paid=total_custody_paid,
        redemption_fee=redemption_fee,
        total_fees=total_fees,
        total_fees_pct=total_fees_pct
    )


def calculate_scenario_1(gold_price_per_gram: float, grams: int) -> ENBDScenarioResult:
    """
    Calculate ENBD Scenario 1: Buy and hold <= 5 years, redeem in year 5.
    
    Args:
        gold_price_per_gram: Gold price in AED per gram
        grams: Number of grams purchased
    
    Returns:
        ENBDScenarioResult for 5-year holding
    """
    return calculate_enbd_scenario(
        gold_price_per_gram=gold_price_per_gram,
        grams=grams,
        holding_years=5,
        scenario_name="Scenario 1: 5-Year Hold"
    )


def calculate_scenario_2(gold_price_per_gram: float, grams: int) -> ENBDScenarioResult:
    """
    Calculate ENBD Scenario 2: Hold > 5 years, redeem in year 10.
    
    Args:
        gold_price_per_gram: Gold price in AED per gram
        grams: Number of grams purchased
    
    Returns:
        ENBDScenarioResult for 10-year holding
    """
    return calculate_enbd_scenario(
        gold_price_per_gram=gold_price_per_gram,
        grams=grams,
        holding_years=10,
        scenario_name="Scenario 2: 10-Year Hold"
    )


def get_fee_schedule_display() -> dict:
    """Get the ENBD fee schedule as a display-friendly dictionary."""
    schedule = ENBDFeeSchedule()
    return {
        "Fee Type": [
            "Acquisition Fee",
            "Arrangement Fee",
            "Custody (Years 1-5)",
            "Custody (Years 6+)",
            "Redemption Fee"
        ],
        "Rate": [
            f"AED {schedule.acquisition_fee_per_gram} per gram",
            f"{float(schedule.arrangement_fee_pct) * 100:.2f}% of notional",
            f"{float(schedule.custody_fee_pct_years_1_5) * 100:.3f}% p.a.",
            f"{float(schedule.custody_fee_pct_years_6_plus) * 100:.2f}% p.a.",
            f"{float(schedule.redemption_fee_pct) * 100:.3f}% of notional"
        ],
        "Payment Timing": [
            "One-time at purchase",
            "One-time at purchase",
            "Accrues yearly, paid at redemption",
            "Accrues yearly, paid at redemption",
            "Paid at redemption"
        ]
    }
