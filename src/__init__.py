"""
Gold Fee Calculator Source Package.
"""

from .fees import (
    calculate_scenario_1,
    calculate_scenario_2,
    calculate_dfm_fees,
    DFMFeeConfig,
    PaymentTiming
)

from .utils import (
    format_aed,
    format_percentage,
    records_to_dataframe,
    create_comparison_df
)

__all__ = [
    "calculate_scenario_1",
    "calculate_scenario_2",
    "calculate_dfm_fees",
    "DFMFeeConfig",
    "PaymentTiming",
    "format_aed",
    "format_percentage",
    "records_to_dataframe",
    "create_comparison_df"
]
