"""
Formatting Utilities

Helper functions for consistent number formatting across the application.
"""

from decimal import Decimal
from typing import Union
import pandas as pd


def format_aed(value: Union[float, Decimal], decimals: int = 4) -> str:
    """
    Format a value as AED currency.
    
    Args:
        value: Numeric value to format
        decimals: Number of decimal places (default 4 for detailed tables)
    
    Returns:
        Formatted string with AED prefix
    """
    if isinstance(value, Decimal):
        value = float(value)
    return f"AED {value:,.{decimals}f}"


def format_percentage(value: Union[float, Decimal], decimals: int = 4) -> str:
    """
    Format a value as percentage.
    
    Args:
        value: Numeric value (already as percentage, not decimal)
        decimals: Number of decimal places
    
    Returns:
        Formatted string with % suffix
    """
    if isinstance(value, Decimal):
        value = float(value)
    return f"{value:.{decimals}f}%"


def format_number(value: Union[float, Decimal], decimals: int = 4) -> str:
    """
    Format a number with specified decimal places.
    
    Args:
        value: Numeric value to format
        decimals: Number of decimal places
    
    Returns:
        Formatted string
    """
    if isinstance(value, Decimal):
        value = float(value)
    return f"{value:,.{decimals}f}"


def create_comparison_df(
    enbd_s1_fees: float,
    enbd_s2_fees: float,
    dfm_fees: float,
    dfm_holding_period: int,
    gold_notional: float
) -> pd.DataFrame:
    """
    Create a comparison DataFrame between ENBD and DFM fees.
    
    Args:
        enbd_s1_fees: ENBD Scenario 1 total fees
        enbd_s2_fees: ENBD Scenario 2 total fees
        dfm_fees: DFM total fees
        dfm_holding_period: DFM holding period in years
        gold_notional: Gold notional value for percentage calculation
    
    Returns:
        DataFrame with comparison metrics
    """
    data = []
    
    # Compare with ENBD Scenario 1 (5-year)
    if dfm_holding_period == 5:
        data.append({
            "Comparison": "DFM vs ENBD (5-year)",
            "ENBD Fees (AED)": enbd_s1_fees,
            "DFM Fees (AED)": dfm_fees,
            "Difference (AED)": dfm_fees - enbd_s1_fees,
            "ENBD % of Notional": (enbd_s1_fees / gold_notional) * 100,
            "DFM % of Notional": (dfm_fees / gold_notional) * 100
        })
    
    # Compare with ENBD Scenario 2 (10-year)
    if dfm_holding_period == 10:
        data.append({
            "Comparison": "DFM vs ENBD (10-year)",
            "ENBD Fees (AED)": enbd_s2_fees,
            "DFM Fees (AED)": dfm_fees,
            "Difference (AED)": dfm_fees - enbd_s2_fees,
            "ENBD % of Notional": (enbd_s2_fees / gold_notional) * 100,
            "DFM % of Notional": (dfm_fees / gold_notional) * 100
        })
    
    # General comparison if holding period is different
    if dfm_holding_period not in [5, 10]:
        data.append({
            "Comparison": f"DFM ({dfm_holding_period}yr) vs ENBD (5yr)",
            "ENBD Fees (AED)": enbd_s1_fees,
            "DFM Fees (AED)": dfm_fees,
            "Difference (AED)": dfm_fees - enbd_s1_fees,
            "ENBD % of Notional": (enbd_s1_fees / gold_notional) * 100,
            "DFM % of Notional": (dfm_fees / gold_notional) * 100
        })
    
    return pd.DataFrame(data)


def style_dataframe(df: pd.DataFrame, precision: int = 4) -> pd.DataFrame:
    """
    Apply consistent styling to a DataFrame for display.
    
    Args:
        df: DataFrame to style
        precision: Decimal precision for numeric columns
    
    Returns:
        Styled DataFrame (or original if styling not supported)
    """
    # Get numeric columns
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    
    # Create a copy with formatted values
    df_display = df.copy()
    for col in numeric_cols:
        if 'AED' in col or 'Value' in col or 'Fee' in col or 'Paid' in col or 'Accrual' in col:
            df_display[col] = df[col].apply(lambda x: f"{x:,.{precision}f}")
        elif '%' in col or 'Pct' in col.lower() or 'Percent' in col.lower():
            df_display[col] = df[col].apply(lambda x: f"{x:.{precision}f}%")
    
    return df_display


def records_to_dataframe(records: list) -> pd.DataFrame:
    """
    Convert a list of fee records to a pandas DataFrame.
    
    Args:
        records: List of YearlyFeeRecord or DFMYearlyRecord objects
    
    Returns:
        DataFrame with fee data
    """
    return pd.DataFrame([r.to_dict() for r in records])
