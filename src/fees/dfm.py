"""
DFM Gold Product Fee Calculator (Configurable)

This module implements a flexible fee calculator for DFM to model
its own proposed gold product economics with configurable parameters.

Features:
- Configurable one-time purchase fees (per gram and percentage)
- Configurable annual custody fee
- Configurable annual management fee
- Configurable redemption fee
- Toggle for fee payment timing (annual vs. at redemption)
"""

from dataclasses import dataclass
from typing import List, Literal
from decimal import Decimal
from enum import Enum


class PaymentTiming(str, Enum):
    """Fee payment timing options."""
    ANNUAL = "Pay annually"
    AT_REDEMPTION = "Accrue and pay at redemption"


@dataclass
class DFMFeeConfig:
    """DFM fee configuration parameters."""
    # One-time purchase fees
    purchase_fee_per_gram: Decimal = Decimal("0")
    purchase_fee_pct: Decimal = Decimal("0")  # As decimal (e.g., 0.021 for 2.1%)
    
    # Annual fees
    custody_fee_pct: Decimal = Decimal("0")  # Annual percentage
    management_fee_pct: Decimal = Decimal("0")  # Annual percentage
    
    # Redemption fee
    redemption_fee_pct: Decimal = Decimal("0")
    
    # Payment timing options
    custody_timing: PaymentTiming = PaymentTiming.AT_REDEMPTION
    management_timing: PaymentTiming = PaymentTiming.AT_REDEMPTION
    
    @classmethod
    def from_enbd_rates(cls) -> "DFMFeeConfig":
        """Create a config matching ENBD rates (for years 1-5)."""
        return cls(
            purchase_fee_per_gram=Decimal("0.1575"),
            purchase_fee_pct=Decimal("0.021"),
            custody_fee_pct=Decimal("0.00315"),
            management_fee_pct=Decimal("0"),
            redemption_fee_pct=Decimal("0.00525"),
            custody_timing=PaymentTiming.AT_REDEMPTION,
            management_timing=PaymentTiming.AT_REDEMPTION
        )


@dataclass
class DFMYearlyRecord:
    """Represents fee breakdown for a single year in DFM model."""
    year: int
    event: str
    gold_value: Decimal
    purchase_fee_gram: Decimal
    purchase_fee_pct: Decimal
    custody_accrual: Decimal
    custody_paid: Decimal
    management_accrual: Decimal
    management_paid: Decimal
    redemption_fee: Decimal
    fees_paid: Decimal
    notes: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame creation."""
        return {
            "Year": self.year,
            "Event": self.event,
            "Gold Value (AED)": float(self.gold_value),
            "Purchase Fee - Per Gram (AED)": float(self.purchase_fee_gram),
            "Purchase Fee - % (AED)": float(self.purchase_fee_pct),
            "Custody Accrual (AED)": float(self.custody_accrual),
            "Custody Paid (AED)": float(self.custody_paid),
            "Mgmt Accrual (AED)": float(self.management_accrual),
            "Mgmt Paid (AED)": float(self.management_paid),
            "Redemption Fee (AED)": float(self.redemption_fee),
            "Fees Paid (AED)": float(self.fees_paid),
            "Notes": self.notes
        }


@dataclass
class DFMCalculationResult:
    """Complete result for a DFM fee calculation."""
    holding_years: int
    gold_price_per_gram: Decimal
    grams: int
    gold_notional: Decimal
    fee_config: DFMFeeConfig
    yearly_records: List[DFMYearlyRecord]
    total_purchase_fees: Decimal
    total_custody_paid: Decimal
    total_management_paid: Decimal
    redemption_fee: Decimal
    total_fees: Decimal
    total_fees_pct: Decimal
    
    def get_summary(self) -> dict:
        """Get summary metrics as dictionary."""
        return {
            "Holding Period (Years)": self.holding_years,
            "Gold Price (AED/gram)": float(self.gold_price_per_gram),
            "Grams Purchased": self.grams,
            "Gold Notional (AED)": float(self.gold_notional),
            "Total Purchase Fees (AED)": float(self.total_purchase_fees),
            "Total Custody Paid (AED)": float(self.total_custody_paid),
            "Total Management Paid (AED)": float(self.total_management_paid),
            "Redemption Fee (AED)": float(self.redemption_fee),
            "Total Fees (AED)": float(self.total_fees),
            "Total Fees (% of Notional)": float(self.total_fees_pct * 100)
        }


def calculate_dfm_fees(
    gold_price_per_gram: float,
    grams: int,
    holding_years: int,
    config: DFMFeeConfig
) -> DFMCalculationResult:
    """
    Calculate DFM gold product fees based on user configuration.
    
    Args:
        gold_price_per_gram: Gold price in AED per gram
        grams: Number of grams purchased
        holding_years: Number of years to hold before redemption
        config: DFM fee configuration parameters
    
    Returns:
        DFMCalculationResult with complete fee breakdown
    """
    # Convert to Decimal for precision
    price = Decimal(str(gold_price_per_gram))
    
    # Calculate gold notional
    gold_notional = price * grams
    
    # Calculate one-time purchase fees
    purchase_fee_gram = config.purchase_fee_per_gram * grams
    purchase_fee_pct = gold_notional * config.purchase_fee_pct
    total_purchase_fees = purchase_fee_gram + purchase_fee_pct
    
    # Calculate redemption fee
    redemption_fee = gold_notional * config.redemption_fee_pct
    
    # Build year-by-year records
    yearly_records = []
    custody_accruals = []
    management_accruals = []
    total_custody_paid = Decimal("0")
    total_management_paid = Decimal("0")
    
    for year in range(holding_years + 1):  # Year 0 to holding_years
        if year == 0:
            # Purchase year
            record = DFMYearlyRecord(
                year=0,
                event="Purchase",
                gold_value=gold_notional,
                purchase_fee_gram=purchase_fee_gram,
                purchase_fee_pct=purchase_fee_pct,
                custody_accrual=Decimal("0"),
                custody_paid=Decimal("0"),
                management_accrual=Decimal("0"),
                management_paid=Decimal("0"),
                redemption_fee=Decimal("0"),
                fees_paid=total_purchase_fees,
                notes="One-time purchase fees paid"
            )
        elif year < holding_years:
            # Holding years (not final year)
            custody_accrual = gold_notional * config.custody_fee_pct
            management_accrual = gold_notional * config.management_fee_pct
            
            custody_accruals.append(custody_accrual)
            management_accruals.append(management_accrual)
            
            # Determine payment based on timing
            if config.custody_timing == PaymentTiming.ANNUAL:
                custody_paid = custody_accrual
                total_custody_paid += custody_paid
                custody_note = "paid"
            else:
                custody_paid = Decimal("0")
                custody_note = "accrued"
            
            if config.management_timing == PaymentTiming.ANNUAL:
                management_paid = management_accrual
                total_management_paid += management_paid
                mgmt_note = "paid"
            else:
                management_paid = Decimal("0")
                mgmt_note = "accrued"
            
            fees_paid = custody_paid + management_paid
            
            notes_parts = []
            if custody_accrual > 0:
                notes_parts.append(f"Custody {custody_note}")
            if management_accrual > 0:
                notes_parts.append(f"Mgmt {mgmt_note}")
            notes = "; ".join(notes_parts) if notes_parts else "No fees this year"
            
            record = DFMYearlyRecord(
                year=year,
                event="Hold",
                gold_value=gold_notional,
                purchase_fee_gram=Decimal("0"),
                purchase_fee_pct=Decimal("0"),
                custody_accrual=custody_accrual,
                custody_paid=custody_paid,
                management_accrual=management_accrual,
                management_paid=management_paid,
                redemption_fee=Decimal("0"),
                fees_paid=fees_paid,
                notes=notes
            )
        else:
            # Redemption year
            custody_accrual = gold_notional * config.custody_fee_pct
            management_accrual = gold_notional * config.management_fee_pct
            
            custody_accruals.append(custody_accrual)
            management_accruals.append(management_accrual)
            
            # Final custody payment
            if config.custody_timing == PaymentTiming.ANNUAL:
                custody_paid = custody_accrual
                total_custody_paid += custody_paid
            else:
                # Pay all accrued custody
                custody_paid = sum(custody_accruals)
                total_custody_paid = custody_paid
            
            # Final management payment
            if config.management_timing == PaymentTiming.ANNUAL:
                management_paid = management_accrual
                total_management_paid += management_paid
            else:
                # Pay all accrued management
                management_paid = sum(management_accruals)
                total_management_paid = management_paid
            
            fees_paid = custody_paid + management_paid + redemption_fee
            
            notes = "Redemption: all due fees paid"
            
            record = DFMYearlyRecord(
                year=year,
                event="Redeem",
                gold_value=gold_notional,
                purchase_fee_gram=Decimal("0"),
                purchase_fee_pct=Decimal("0"),
                custody_accrual=custody_accrual,
                custody_paid=custody_paid,
                management_accrual=management_accrual,
                management_paid=management_paid,
                redemption_fee=redemption_fee,
                fees_paid=fees_paid,
                notes=notes
            )
        
        yearly_records.append(record)
    
    # Calculate totals
    total_fees = total_purchase_fees + total_custody_paid + total_management_paid + redemption_fee
    total_fees_pct = total_fees / gold_notional if gold_notional > 0 else Decimal("0")
    
    return DFMCalculationResult(
        holding_years=holding_years,
        gold_price_per_gram=price,
        grams=grams,
        gold_notional=gold_notional,
        fee_config=config,
        yearly_records=yearly_records,
        total_purchase_fees=total_purchase_fees,
        total_custody_paid=total_custody_paid,
        total_management_paid=total_management_paid,
        redemption_fee=redemption_fee,
        total_fees=total_fees,
        total_fees_pct=total_fees_pct
    )


def get_dfm_config_display(config: DFMFeeConfig) -> dict:
    """Get the DFM fee configuration as a display-friendly dictionary."""
    return {
        "Fee Type": [
            "Purchase Fee (per gram)",
            "Purchase Fee (%)",
            "Annual Custody Fee",
            "Annual Management Fee",
            "Redemption Fee"
        ],
        "Rate": [
            f"AED {config.purchase_fee_per_gram}",
            f"{float(config.purchase_fee_pct) * 100:.3f}%",
            f"{float(config.custody_fee_pct) * 100:.3f}% p.a.",
            f"{float(config.management_fee_pct) * 100:.3f}% p.a.",
            f"{float(config.redemption_fee_pct) * 100:.3f}%"
        ],
        "Payment Timing": [
            "One-time at purchase",
            "One-time at purchase",
            config.custody_timing.value,
            config.management_timing.value,
            "Paid at redemption"
        ]
    }
