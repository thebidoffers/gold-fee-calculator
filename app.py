"""
Gold Product Fee Calculator & Modelling Tool

A production-quality Streamlit web app for Dubai Financial Market (DFM)
to benchmark against ENBD gold product fees and model custom fee structures.

Author: DFM Product Team
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
from decimal import Decimal
import io

# Import calculation modules
from src.fees.enbd import (
    calculate_scenario_1,
    calculate_scenario_2,
    get_fee_schedule_display
)
from src.fees.dfm import (
    DFMFeeConfig,
    PaymentTiming,
    calculate_dfm_fees,
    get_dfm_config_display
)
from src.utils.formatting import (
    records_to_dataframe,
    create_comparison_df
)


# Page configuration
st.set_page_config(
    page_title="Gold Fee Calculator | DFM",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better presentation
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🥇 Gold Product Fee Calculator & Modelling Tool</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Dubai Financial Market | Internal Product Design & Benchmarking</p>', unsafe_allow_html=True)

st.divider()


def format_df_for_display(df: pd.DataFrame, precision: int = 4) -> pd.DataFrame:
    """Format DataFrame for display with proper number formatting."""
    df_display = df.copy()
    for col in df_display.columns:
        if df_display[col].dtype in ['float64', 'int64']:
            if 'Year' in col:
                df_display[col] = df_display[col].astype(int)
            elif '%' in col or 'Pct' in col.lower():
                df_display[col] = df_display[col].apply(lambda x: f"{x:.{precision}f}%")
            else:
                df_display[col] = df_display[col].apply(lambda x: f"{x:,.{precision}f}")
    return df_display


def display_summary_metrics(result, prefix: str = ""):
    """Display summary metrics in columns."""
    summary = result.get_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            f"{prefix}Total Fees",
            f"AED {float(result.total_fees):,.4f}",
            help="Sum of all fees paid over the holding period"
        )
    
    with col2:
        st.metric(
            f"{prefix}Fees % of Notional",
            f"{float(result.total_fees_pct) * 100:.4f}%",
            help="Total fees as percentage of gold notional value"
        )
    
    with col3:
        st.metric(
            "Gold Notional",
            f"AED {float(result.gold_notional):,.2f}",
            help="Gold price × grams purchased"
        )
    
    with col4:
        if hasattr(result, 'scenario_name'):
            st.metric("Holding Period", f"{result.holding_years} Years")
        else:
            st.metric("Holding Period", f"{result.holding_years} Years")


def create_csv_download(df: pd.DataFrame, filename: str) -> bytes:
    """Create CSV bytes for download."""
    return df.to_csv(index=False).encode('utf-8')


# Main tabs
tab1, tab2 = st.tabs(["📊 ENBD Benchmark", "⚙️ DFM Fee Modelling"])


# ============================================================================
# TAB 1: ENBD BENCHMARK
# ============================================================================
with tab1:
    st.header("ENBD Precious Metal – Gold Fee Benchmark")
    st.markdown("""
    This section replicates the **ENBD Precious Metal – Gold** fee logic for benchmarking.
    Two scenarios are calculated: a 5-year hold and a 10-year hold.
    """)
    
    # ENBD Fee Schedule Display
    with st.expander("📋 View ENBD Fee Schedule (Fixed)", expanded=False):
        fee_schedule = get_fee_schedule_display()
        st.table(pd.DataFrame(fee_schedule))
        st.caption("*Note: ENBD documentation states 'up to 2.1%' for arrangement fee; 2.1% is used for benchmarking.*")
    
    st.divider()
    
    # User inputs
    st.subheader("Input Parameters")
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        enbd_gold_price = st.number_input(
            "Gold Price (AED per gram)",
            min_value=1.0,
            max_value=10000.0,
            value=596.00,
            step=0.01,
            format="%.2f",
            help="Enter the gold price in AED per gram",
            key="enbd_gold_price"
        )
    
    with col_input2:
        enbd_grams = st.number_input(
            "Grams Purchased",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
            help="Number of grams to purchase (1-100)",
            key="enbd_grams"
        )
    
    # Display calculated notional
    enbd_notional = enbd_gold_price * enbd_grams
    st.info(f"**Gold Notional Value:** AED {enbd_notional:,.2f} ({enbd_grams} gram{'s' if enbd_grams > 1 else ''} × AED {enbd_gold_price:,.2f}/gram)")
    
    st.divider()
    
    # Calculate both scenarios
    scenario_1 = calculate_scenario_1(enbd_gold_price, enbd_grams)
    scenario_2 = calculate_scenario_2(enbd_gold_price, enbd_grams)
    
    # Display scenarios side by side
    col_s1, col_s2 = st.columns(2)
    
    # Scenario 1
    with col_s1:
        st.subheader("📈 Scenario 1: 5-Year Hold")
        st.caption("Buy and hold ≤5 years, redeem in year 5")
        
        display_summary_metrics(scenario_1)
        
        # Fee breakdown
        st.markdown("**Fee Breakdown:**")
        breakdown_col1, breakdown_col2 = st.columns(2)
        with breakdown_col1:
            st.write(f"• Purchase Fees: AED {float(scenario_1.total_purchase_fees):,.4f}")
            st.write(f"• Total Custody: AED {float(scenario_1.total_custody_paid):,.4f}")
        with breakdown_col2:
            st.write(f"• Redemption Fee: AED {float(scenario_1.redemption_fee):,.4f}")
        
        # Year-by-year table
        st.markdown("**Year-by-Year Fee Schedule:**")
        df_s1 = records_to_dataframe(scenario_1.yearly_records)
        st.dataframe(
            format_df_for_display(df_s1),
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv_s1 = create_csv_download(df_s1, "enbd_scenario_1.csv")
        st.download_button(
            label="📥 Download Scenario 1 (CSV)",
            data=csv_s1,
            file_name="enbd_scenario_1.csv",
            mime="text/csv",
            key="download_s1"
        )
    
    # Scenario 2
    with col_s2:
        st.subheader("📈 Scenario 2: 10-Year Hold")
        st.caption("Hold >5 years, redeem in year 10 (higher custody rate for years 6+)")
        
        display_summary_metrics(scenario_2)
        
        # Fee breakdown
        st.markdown("**Fee Breakdown:**")
        breakdown_col1, breakdown_col2 = st.columns(2)
        with breakdown_col1:
            st.write(f"• Purchase Fees: AED {float(scenario_2.total_purchase_fees):,.4f}")
            st.write(f"• Total Custody: AED {float(scenario_2.total_custody_paid):,.4f}")
        with breakdown_col2:
            st.write(f"• Redemption Fee: AED {float(scenario_2.redemption_fee):,.4f}")
        
        # Year-by-year table
        st.markdown("**Year-by-Year Fee Schedule:**")
        df_s2 = records_to_dataframe(scenario_2.yearly_records)
        st.dataframe(
            format_df_for_display(df_s2),
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv_s2 = create_csv_download(df_s2, "enbd_scenario_2.csv")
        st.download_button(
            label="📥 Download Scenario 2 (CSV)",
            data=csv_s2,
            file_name="enbd_scenario_2.csv",
            mime="text/csv",
            key="download_s2"
        )
    
    # Validation display
    with st.expander("🔍 Validation Check (1 gram @ AED 596)", expanded=False):
        if enbd_grams == 1 and enbd_gold_price == 596.0:
            st.success("✅ Using validation parameters (1 gram @ AED 596)")
        else:
            st.info("ℹ️ Validation values are calculated for 1 gram @ AED 596 for reference:")
        
        val_s1 = calculate_scenario_1(596.0, 1)
        val_s2 = calculate_scenario_2(596.0, 1)
        
        st.markdown("""
        **Scenario 1 (5-Year) Expected Values:**
        - Acquisition Fee: AED 0.1575 ✓
        - Arrangement Fee: AED 12.5160 (596 × 2.1%) ✓
        - Custody per year (Years 1-5): AED 1.8774 (596 × 0.315%) ✓
        - Total Custody (5 years): AED 9.3870 ✓
        - Redemption Fee: AED 3.1290 (596 × 0.525%) ✓
        - **Total Fees: AED 25.1895** ✓
        """)
        
        st.write(f"Calculated Total: AED {float(val_s1.total_fees):,.4f}")
        
        st.markdown("""
        **Scenario 2 (10-Year) Expected Values:**
        - Custody Years 1-5: AED 9.3870 (5 × 1.8774)
        - Custody Years 6-10: AED 31.2900 (5 × 596 × 1.05%)
        - Total Custody: AED 40.6770
        """)
        
        st.write(f"Calculated Custody Total: AED {float(val_s2.total_custody_paid):,.4f}")
        st.write(f"Calculated Total Fees: AED {float(val_s2.total_fees):,.4f}")


# ============================================================================
# TAB 2: DFM FEE MODELLING
# ============================================================================
with tab2:
    st.header("DFM Fee Modelling Tool")
    st.markdown("""
    Configure custom fee structures for DFM's proposed gold product.
    Compare against ENBD benchmarks to evaluate competitiveness.
    """)
    
    st.divider()
    
    # Two-column layout: inputs on left, results on right
    col_config, col_results = st.columns([1, 2])
    
    with col_config:
        st.subheader("⚙️ Configuration")
        
        # Basic inputs
        st.markdown("**Product Parameters**")
        dfm_gold_price = st.number_input(
            "Gold Price (AED per gram)",
            min_value=1.0,
            max_value=10000.0,
            value=596.00,
            step=0.01,
            format="%.2f",
            help="Gold price in AED per gram",
            key="dfm_gold_price"
        )
        
        dfm_grams = st.number_input(
            "Grams Purchased",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
            help="Number of grams (1-100)",
            key="dfm_grams"
        )
        
        dfm_holding_period = st.selectbox(
            "Holding Period (Years)",
            options=[1, 2, 3, 5, 10],
            index=3,  # Default to 5 years
            help="Select the holding period for fee modelling",
            key="dfm_holding"
        )
        
        st.divider()
        
        # Fee configuration
        st.markdown("**Fee Structure**")
        
        # Match ENBD button
        if st.button("📋 Match ENBD Rates", help="Set DFM fees to match ENBD benchmark rates"):
            st.session_state['dfm_purchase_gram'] = 0.1575
            st.session_state['dfm_purchase_pct'] = 2.1
            st.session_state['dfm_custody'] = 0.315
            st.session_state['dfm_management'] = 0.0
            st.session_state['dfm_redemption'] = 0.525
            st.rerun()
        
        # Initialize session state for fee inputs
        if 'dfm_purchase_gram' not in st.session_state:
            st.session_state['dfm_purchase_gram'] = 0.0
        if 'dfm_purchase_pct' not in st.session_state:
            st.session_state['dfm_purchase_pct'] = 0.0
        if 'dfm_custody' not in st.session_state:
            st.session_state['dfm_custody'] = 0.0
        if 'dfm_management' not in st.session_state:
            st.session_state['dfm_management'] = 0.0
        if 'dfm_redemption' not in st.session_state:
            st.session_state['dfm_redemption'] = 0.0
        
        # One-time purchase fees
        dfm_purchase_gram = st.number_input(
            "Purchase Fee (AED per gram)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state['dfm_purchase_gram'],
            step=0.01,
            format="%.4f",
            help="One-time fee per gram at purchase",
            key="dfm_purchase_gram_input"
        )
        
        dfm_purchase_pct = st.number_input(
            "Purchase Fee (% of notional)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state['dfm_purchase_pct'],
            step=0.01,
            format="%.3f",
            help="One-time percentage fee at purchase",
            key="dfm_purchase_pct_input"
        )
        
        # Annual fees
        dfm_custody = st.number_input(
            "Annual Custody Fee (% p.a.)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state['dfm_custody'],
            step=0.01,
            format="%.3f",
            help="Annual custody/insurance fee as percentage",
            key="dfm_custody_input"
        )
        
        dfm_management = st.number_input(
            "Annual Management Fee (% p.a.)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state['dfm_management'],
            step=0.01,
            format="%.3f",
            help="Optional annual management fee",
            key="dfm_management_input"
        )
        
        # Redemption fee
        dfm_redemption = st.number_input(
            "Redemption Fee (% of notional)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state['dfm_redemption'],
            step=0.01,
            format="%.3f",
            help="Fee charged at redemption",
            key="dfm_redemption_input"
        )
        
        st.divider()
        
        # Payment timing toggles
        st.markdown("**Payment Timing**")
        
        custody_timing = st.radio(
            "Custody Fee Payment",
            options=[PaymentTiming.ANNUAL.value, PaymentTiming.AT_REDEMPTION.value],
            index=1,  # Default to "at redemption"
            help="When custody fees are paid",
            key="custody_timing"
        )
        
        management_timing = st.radio(
            "Management Fee Payment",
            options=[PaymentTiming.ANNUAL.value, PaymentTiming.AT_REDEMPTION.value],
            index=1,
            help="When management fees are paid",
            key="management_timing"
        )
    
    # Build DFM configuration
    dfm_config = DFMFeeConfig(
        purchase_fee_per_gram=Decimal(str(dfm_purchase_gram)),
        purchase_fee_pct=Decimal(str(dfm_purchase_pct / 100)),  # Convert % to decimal
        custody_fee_pct=Decimal(str(dfm_custody / 100)),
        management_fee_pct=Decimal(str(dfm_management / 100)),
        redemption_fee_pct=Decimal(str(dfm_redemption / 100)),
        custody_timing=PaymentTiming.ANNUAL if custody_timing == PaymentTiming.ANNUAL.value else PaymentTiming.AT_REDEMPTION,
        management_timing=PaymentTiming.ANNUAL if management_timing == PaymentTiming.ANNUAL.value else PaymentTiming.AT_REDEMPTION
    )
    
    # Calculate DFM fees
    dfm_result = calculate_dfm_fees(
        gold_price_per_gram=dfm_gold_price,
        grams=dfm_grams,
        holding_years=dfm_holding_period,
        config=dfm_config
    )
    
    # Results section
    with col_results:
        st.subheader("📊 Results")
        
        # Validation warning
        if dfm_holding_period < 1:
            st.warning("⚠️ Holding period must be at least 1 year.")
        
        # Display notional
        dfm_notional = dfm_gold_price * dfm_grams
        st.info(f"**Gold Notional Value:** AED {dfm_notional:,.2f} ({dfm_grams} gram{'s' if dfm_grams > 1 else ''} × AED {dfm_gold_price:,.2f}/gram)")
        
        # Summary metrics
        display_summary_metrics(dfm_result, prefix="DFM ")
        
        # Fee breakdown
        st.markdown("**DFM Fee Breakdown:**")
        fee_col1, fee_col2 = st.columns(2)
        with fee_col1:
            st.write(f"• Purchase Fees: AED {float(dfm_result.total_purchase_fees):,.4f}")
            st.write(f"• Total Custody: AED {float(dfm_result.total_custody_paid):,.4f}")
        with fee_col2:
            st.write(f"• Total Management: AED {float(dfm_result.total_management_paid):,.4f}")
            st.write(f"• Redemption Fee: AED {float(dfm_result.redemption_fee):,.4f}")
        
        # Fee config display
        with st.expander("📋 View Current Fee Configuration", expanded=False):
            config_display = get_dfm_config_display(dfm_config)
            st.table(pd.DataFrame(config_display))
        
        st.divider()
        
        # Year-by-year table
        st.markdown("**Year-by-Year Fee Schedule:**")
        df_dfm = records_to_dataframe(dfm_result.yearly_records)
        st.dataframe(
            format_df_for_display(df_dfm),
            use_container_width=True,
            hide_index=True
        )
        
        # Download button for DFM
        csv_dfm = create_csv_download(df_dfm, "dfm_fee_model.csv")
        st.download_button(
            label="📥 Download DFM Model (CSV)",
            data=csv_dfm,
            file_name="dfm_fee_model.csv",
            mime="text/csv",
            key="download_dfm"
        )
        
        st.divider()
        
        # Comparison Panel
        st.subheader("📊 Comparison: DFM vs ENBD")
        
        # Calculate ENBD scenarios for comparison (using DFM parameters)
        enbd_s1_compare = calculate_scenario_1(dfm_gold_price, dfm_grams)
        enbd_s2_compare = calculate_scenario_2(dfm_gold_price, dfm_grams)
        
        # Create comparison table
        comparison_data = []
        
        # Always show comparison with 5-year ENBD
        comparison_data.append({
            "Comparison": f"DFM ({dfm_holding_period}yr) vs ENBD (5yr)",
            "DFM Fees (AED)": float(dfm_result.total_fees),
            "ENBD Fees (AED)": float(enbd_s1_compare.total_fees),
            "Difference (AED)": float(dfm_result.total_fees) - float(enbd_s1_compare.total_fees),
            "DFM % of Notional": float(dfm_result.total_fees_pct) * 100,
            "ENBD % of Notional": float(enbd_s1_compare.total_fees_pct) * 100
        })
        
        # Add 10-year comparison if relevant
        if dfm_holding_period == 10:
            comparison_data.append({
                "Comparison": "DFM (10yr) vs ENBD (10yr)",
                "DFM Fees (AED)": float(dfm_result.total_fees),
                "ENBD Fees (AED)": float(enbd_s2_compare.total_fees),
                "Difference (AED)": float(dfm_result.total_fees) - float(enbd_s2_compare.total_fees),
                "DFM % of Notional": float(dfm_result.total_fees_pct) * 100,
                "ENBD % of Notional": float(enbd_s2_compare.total_fees_pct) * 100
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(
            format_df_for_display(df_comparison, precision=4),
            use_container_width=True,
            hide_index=True
        )
        
        # Visual comparison
        col_dfm, col_enbd = st.columns(2)
        
        with col_dfm:
            st.metric(
                "DFM Total Fees",
                f"AED {float(dfm_result.total_fees):,.4f}",
                f"{float(dfm_result.total_fees_pct) * 100:.4f}% of notional"
            )
        
        with col_enbd:
            # Show appropriate ENBD benchmark
            if dfm_holding_period <= 5:
                st.metric(
                    "ENBD (5yr) Total Fees",
                    f"AED {float(enbd_s1_compare.total_fees):,.4f}",
                    f"{float(enbd_s1_compare.total_fees_pct) * 100:.4f}% of notional"
                )
            else:
                st.metric(
                    "ENBD (10yr) Total Fees",
                    f"AED {float(enbd_s2_compare.total_fees):,.4f}",
                    f"{float(enbd_s2_compare.total_fees_pct) * 100:.4f}% of notional"
                )
        
        # Competitive assessment
        if dfm_holding_period <= 5:
            enbd_benchmark = float(enbd_s1_compare.total_fees)
        else:
            enbd_benchmark = float(enbd_s2_compare.total_fees)
        
        difference = float(dfm_result.total_fees) - enbd_benchmark
        
        if difference < 0:
            st.success(f"✅ DFM is **more competitive** by AED {abs(difference):,.4f} ({abs(difference)/enbd_benchmark*100:.2f}% lower)")
        elif difference > 0:
            st.warning(f"⚠️ DFM is **less competitive** by AED {difference:,.4f} ({difference/enbd_benchmark*100:.2f}% higher)")
        else:
            st.info("➡️ DFM fees match ENBD exactly")


# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9rem;">
    <p>Gold Product Fee Calculator & Modelling Tool v1.0.0</p>
    <p>Dubai Financial Market | Internal Use Only</p>
</div>
""", unsafe_allow_html=True)
