"""
Gold Product Fee Calculator & Modelling Tool

A production-quality Streamlit web application for Dubai Financial Market (DFM)
to benchmark against ENBD gold product fees and model custom fee structures.

Author: DFM Product Team
Version: 1.1.0
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
    .metric-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E3A5F;
    }
    .scenario-header {
        background-color: #e8f4ea;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem;
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


def display_summary_metrics_clean(result, scenario_name: str = ""):
    """Display summary metrics in a clean, readable format."""
    
    st.markdown(f"### 📊 {scenario_name} Summary")
    
    # Create two rows of metrics for better readability
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Total Fees</div>
            <div class="metric-value">AED {float(result.total_fees):,.4f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Fees as % of Notional</div>
            <div class="metric-value">{float(result.total_fees_pct) * 100:.4f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Gold Notional</div>
            <div class="metric-value">AED {float(result.gold_notional):,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Holding Period</div>
            <div class="metric-value">{result.holding_years} Years</div>
        </div>
        """, unsafe_allow_html=True)


def display_fee_breakdown(result):
    """Display fee breakdown in a clean table format."""
    
    st.markdown("#### 💰 Fee Breakdown")
    
    breakdown_data = {
        "Fee Type": ["Purchase Fees", "Total Custody", "Redemption Fee", "**TOTAL FEES**"],
        "Amount (AED)": [
            f"{float(result.total_purchase_fees):,.4f}",
            f"{float(result.total_custody_paid):,.4f}",
            f"{float(result.redemption_fee):,.4f}",
            f"**{float(result.total_fees):,.4f}**"
        ]
    }
    
    st.table(pd.DataFrame(breakdown_data))


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
    st.subheader("📝 Input Parameters")
    col_input1, col_input2, col_input3 = st.columns([1, 1, 2])
    
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
    
    with col_input3:
        # Display calculated notional
        enbd_notional = enbd_gold_price * enbd_grams
        st.markdown("**Calculated Gold Notional:**")
        st.success(f"AED {enbd_notional:,.2f} ({enbd_grams} gram{'s' if enbd_grams > 1 else ''} × AED {enbd_gold_price:,.2f}/gram)")
    
    st.divider()
    
    # Calculate both scenarios
    scenario_1 = calculate_scenario_1(enbd_gold_price, enbd_grams)
    scenario_2 = calculate_scenario_2(enbd_gold_price, enbd_grams)
    
    # Display scenarios in separate sections (not side by side for better readability)
    st.markdown("---")
    
    # ===================== SCENARIO 1 =====================
    st.markdown("""
    <div class="scenario-header">
        <h2>📈 Scenario 1: 5-Year Hold</h2>
        <p>Buy and hold ≤5 years, redeem in year 5 | Custody rate: 0.315% p.a.</p>
    </div>
    """, unsafe_allow_html=True)
    
    display_summary_metrics_clean(scenario_1, "5-Year Hold")
    
    st.markdown("")
    display_fee_breakdown(scenario_1)
    
    # Year-by-year table
    st.markdown("#### 📅 Year-by-Year Fee Schedule")
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
    
    st.markdown("---")
    
    # ===================== SCENARIO 2 =====================
    st.markdown("""
    <div class="scenario-header">
        <h2>📈 Scenario 2: 10-Year Hold</h2>
        <p>Hold >5 years, redeem in year 10 | Custody rate: 0.315% (years 1-5), 1.05% (years 6-10)</p>
    </div>
    """, unsafe_allow_html=True)
    
    display_summary_metrics_clean(scenario_2, "10-Year Hold")
    
    st.markdown("")
    display_fee_breakdown(scenario_2)
    
    # Year-by-year table
    st.markdown("#### 📅 Year-by-Year Fee Schedule")
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
    
    st.markdown("---")
    
    # ===================== SIDE-BY-SIDE COMPARISON =====================
    st.markdown("### 📊 Scenario Comparison")
    
    comparison_table = pd.DataFrame({
        "Metric": ["Total Fees (AED)", "Fees % of Notional", "Purchase Fees (AED)", "Total Custody (AED)", "Redemption Fee (AED)"],
        "Scenario 1 (5-Year)": [
            f"{float(scenario_1.total_fees):,.4f}",
            f"{float(scenario_1.total_fees_pct) * 100:.4f}%",
            f"{float(scenario_1.total_purchase_fees):,.4f}",
            f"{float(scenario_1.total_custody_paid):,.4f}",
            f"{float(scenario_1.redemption_fee):,.4f}"
        ],
        "Scenario 2 (10-Year)": [
            f"{float(scenario_2.total_fees):,.4f}",
            f"{float(scenario_2.total_fees_pct) * 100:.4f}%",
            f"{float(scenario_2.total_purchase_fees):,.4f}",
            f"{float(scenario_2.total_custody_paid):,.4f}",
            f"{float(scenario_2.redemption_fee):,.4f}"
        ]
    })
    
    st.table(comparison_table)
    
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
    
    # Configuration section
    st.subheader("⚙️ Configuration")
    
    # Basic inputs in a clean row
    st.markdown("**Product Parameters**")
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
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
    
    with col_p2:
        dfm_grams = st.number_input(
            "Grams Purchased",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
            help="Number of grams (1-100)",
            key="dfm_grams"
        )
    
    with col_p3:
        dfm_holding_period = st.selectbox(
            "Holding Period (Years)",
            options=[1, 2, 3, 5, 10],
            index=3,  # Default to 5 years
            help="Select the holding period for fee modelling",
            key="dfm_holding"
        )
    
    # Display notional
    dfm_notional = dfm_gold_price * dfm_grams
    st.success(f"**Gold Notional Value:** AED {dfm_notional:,.2f}")
    
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
    
    # Fee inputs in organized rows
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.markdown("**One-Time Fees**")
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
    
    with col_f2:
        st.markdown("**Annual Fees**")
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
        
        st.markdown("**Payment Timing**")
        custody_timing = st.radio(
            "Custody Fee Payment",
            options=[PaymentTiming.ANNUAL.value, PaymentTiming.AT_REDEMPTION.value],
            index=1,
            help="When custody fees are paid",
            key="custody_timing",
            horizontal=True
        )
        
        management_timing = st.radio(
            "Management Fee Payment",
            options=[PaymentTiming.ANNUAL.value, PaymentTiming.AT_REDEMPTION.value],
            index=1,
            help="When management fees are paid",
            key="management_timing",
            horizontal=True
        )
    
    # Build DFM configuration
    dfm_config = DFMFeeConfig(
        purchase_fee_per_gram=Decimal(str(dfm_purchase_gram)),
        purchase_fee_pct=Decimal(str(dfm_purchase_pct / 100)),
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
    
    st.divider()
    
    # ===================== RESULTS SECTION =====================
    st.subheader("📊 Results")
    
    # Validation warning
    if dfm_holding_period < 1:
        st.warning("⚠️ Holding period must be at least 1 year.")
    
    # Summary metrics
    display_summary_metrics_clean(dfm_result, f"DFM {dfm_holding_period}-Year Model")
    
    # Fee breakdown
    st.markdown("#### 💰 Fee Breakdown")
    
    dfm_breakdown = pd.DataFrame({
        "Fee Type": ["Purchase Fees", "Total Custody", "Total Management", "Redemption Fee", "**TOTAL FEES**"],
        "Amount (AED)": [
            f"{float(dfm_result.total_purchase_fees):,.4f}",
            f"{float(dfm_result.total_custody_paid):,.4f}",
            f"{float(dfm_result.total_management_paid):,.4f}",
            f"{float(dfm_result.redemption_fee):,.4f}",
            f"**{float(dfm_result.total_fees):,.4f}**"
        ]
    })
    st.table(dfm_breakdown)
    
    # Fee config display
    with st.expander("📋 View Current Fee Configuration", expanded=False):
        config_display = get_dfm_config_display(dfm_config)
        st.table(pd.DataFrame(config_display))
    
    # Year-by-year table
    st.markdown("#### 📅 Year-by-Year Fee Schedule")
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
    
    # ===================== COMPARISON SECTION =====================
    st.subheader("📊 Comparison: DFM vs ENBD")
    
    # Calculate ENBD scenarios for comparison
    enbd_s1_compare = calculate_scenario_1(dfm_gold_price, dfm_grams)
    enbd_s2_compare = calculate_scenario_2(dfm_gold_price, dfm_grams)
    
    # Determine appropriate benchmark
    if dfm_holding_period <= 5:
        enbd_benchmark = enbd_s1_compare
        benchmark_name = "ENBD 5-Year"
    else:
        enbd_benchmark = enbd_s2_compare
        benchmark_name = "ENBD 10-Year"
    
    # Comparison table
    comparison_data = pd.DataFrame({
        "Metric": [
            "Total Fees (AED)",
            "Fees % of Notional",
            "Purchase Fees (AED)",
            "Total Custody (AED)",
            "Redemption Fee (AED)"
        ],
        f"DFM ({dfm_holding_period}-Year)": [
            f"{float(dfm_result.total_fees):,.4f}",
            f"{float(dfm_result.total_fees_pct) * 100:.4f}%",
            f"{float(dfm_result.total_purchase_fees):,.4f}",
            f"{float(dfm_result.total_custody_paid):,.4f}",
            f"{float(dfm_result.redemption_fee):,.4f}"
        ],
        benchmark_name: [
            f"{float(enbd_benchmark.total_fees):,.4f}",
            f"{float(enbd_benchmark.total_fees_pct) * 100:.4f}%",
            f"{float(enbd_benchmark.total_purchase_fees):,.4f}",
            f"{float(enbd_benchmark.total_custody_paid):,.4f}",
            f"{float(enbd_benchmark.redemption_fee):,.4f}"
        ]
    })
    
    st.table(comparison_data)
    
    # Competitive assessment
    difference = float(dfm_result.total_fees) - float(enbd_benchmark.total_fees)
    enbd_fees = float(enbd_benchmark.total_fees)
    
    st.markdown("#### 🎯 Competitive Assessment")
    
    if difference < -0.001:
        pct_lower = abs(difference) / enbd_fees * 100 if enbd_fees > 0 else 0
        st.success(f"✅ **DFM is MORE COMPETITIVE** by AED {abs(difference):,.4f} ({pct_lower:.2f}% lower than {benchmark_name})")
    elif difference > 0.001:
        pct_higher = difference / enbd_fees * 100 if enbd_fees > 0 else 0
        st.warning(f"⚠️ **DFM is LESS COMPETITIVE** by AED {difference:,.4f} ({pct_higher:.2f}% higher than {benchmark_name})")
    else:
        st.info(f"➡️ **DFM fees MATCH** {benchmark_name} exactly")


# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9rem;">
    <p>Gold Product Fee Calculator & Modelling Tool v1.1.0</p>
    <p>Dubai Financial Market | Internal Use Only</p>
</div>
""", unsafe_allow_html=True)
