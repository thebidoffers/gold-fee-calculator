# 🥇 Gold Product Fee Calculator & Modelling Tool

A production-quality Streamlit web application for Dubai Financial Market (DFM) to benchmark gold product fees against ENBD and model custom fee structures.

## Overview

This tool provides:
- **ENBD Benchmark Section**: Fixed fee logic replicating ENBD's "Precious Metal – Gold" product
- **DFM Fee Modelling Section**: Configurable fee structure for DFM product design

## Features

### ENBD Benchmark
- Calculates fees for two scenarios:
  - **Scenario 1**: 5-year hold (custody at 0.315% p.a.)
  - **Scenario 2**: 10-year hold (custody at 1.05% p.a. for years 6+)
- Year-by-year fee breakdown with transparent calculations
- CSV export for both scenarios

### DFM Fee Modelling
- Fully configurable fee parameters:
  - One-time purchase fees (per gram and percentage)
  - Annual custody fee (% p.a.)
  - Annual management fee (% p.a.)
  - Redemption fee (%)
- Payment timing toggles (annual vs. at redemption)
- Quick "Match ENBD Rates" button for easy benchmarking
- Side-by-side comparison with ENBD benchmarks
- CSV export for fee model

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup Steps

1. **Clone or download the repository**
```bash
cd gold-fee-calculator
```

2. **Create a virtual environment** (recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Running Tests

To run the unit tests:

```bash
# From the project root directory
pytest tests/ -v
```

Or run a specific test file:
```bash
pytest tests/test_fees.py -v
```

## Project Structure

```
gold-fee-calculator/
├── app.py                    # Streamlit entry point
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── src/
│   ├── __init__.py
│   ├── fees/
│   │   ├── __init__.py
│   │   ├── enbd.py          # ENBD fee schedule & calculations
│   │   └── dfm.py           # DFM configurable fee engine
│   └── utils/
│       ├── __init__.py
│       └── formatting.py     # Display formatting helpers
└── tests/
    ├── __init__.py
    └── test_fees.py          # Unit tests for fee calculations
```

## ENBD Fee Schedule (Fixed)

| Fee Type | Rate | Payment Timing |
|----------|------|----------------|
| Acquisition Fee | AED 0.1575 per gram | One-time at purchase |
| Arrangement Fee | 2.10% of notional* | One-time at purchase |
| Custody (Years 1-5) | 0.315% p.a. | Accrues yearly, paid at redemption |
| Custody (Years 6+) | 1.05% p.a. | Accrues yearly, paid at redemption |
| Redemption Fee | 0.525% of notional | Paid at redemption |

*Note: ENBD documentation states "up to 2.1%"; 2.1% is used for benchmarking.

## Validation

The application includes built-in validation for the benchmark case (1 gram @ AED 596):

**Scenario 1 (5-Year Hold)**
- Acquisition Fee: AED 0.1575
- Arrangement Fee: AED 12.5160
- Custody (5 years): AED 9.3870
- Redemption Fee: AED 3.1290
- **Total Fees: AED 25.1895**

**Scenario 2 (10-Year Hold)**
- Purchase Fees: AED 12.6735
- Custody Years 1-5: AED 9.3870
- Custody Years 6-10: AED 31.2900
- Redemption Fee: AED 3.1290
- **Total Fees: AED 56.4795**

## Technical Notes

- All calculations use Python's `Decimal` type for precision
- Fee accrual and payment timing are explicitly modeled
- Gold notional is assumed constant for fee calculations
- Display values shown to 4 decimal places in tables, 2 in summaries

## Usage Tips

1. **Benchmarking**: Start with the ENBD Benchmark tab to understand the competitive landscape
2. **Quick Comparison**: Use the "Match ENBD Rates" button in DFM section, then adjust individual parameters
3. **Export**: Use CSV download buttons to export tables for presentations
4. **Validation**: Check the validation expander in ENBD tab to verify calculations

## Support

For questions or issues, contact the DFM Product Team.

---

*Gold Product Fee Calculator & Modelling Tool v1.0.0*  
*Dubai Financial Market | Internal Use Only*
