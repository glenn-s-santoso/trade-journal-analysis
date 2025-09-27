# Bybit Closed PnL Analyzer

A tool to fetch and analyze your closed PnL from Bybit for the past week. This helps with conducting a retrospective review of your trading performance.

## Setup

1. Create a virtual environment (if not already created):
   ```
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your API credentials:
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your Bybit API key and secret
   - If you encounter SSL verification errors, set `DISABLE_SSL_VERIFY=true` in your `.env` file

## Usage

### Basic Analysis

For quick command-line analysis:
```
python get_closed_pnl.py
```

This will:
1. Fetch your closed PnL data from Bybit for the past week
2. Display detailed analysis statistics in the console
3. Generate visualizations of your PnL performance
4. Save the raw data to `closed_pnl_data.csv`
5. Save the visualizations to `pnl_analysis.png`

### Detailed HTML Report

For a comprehensive HTML report with insights and recommendations:
```
python generate_report.py
```

This will:
1. Fetch your closed PnL data from Bybit
2. Generate an interactive HTML report (`trading_report.html`)
3. Include performance metrics, charts, and actionable recommendations
4. Save visualization images in the `report_plots` directory

### AI-Enhanced Trading Report

For an advanced report with AI analysis of your trading patterns:
```
python generate_llm_report.py
```

This will:
1. Fetch your closed PnL data from Bybit
2. Use OpenRouter API to analyze your trading performance with AI
3. Generate an enhanced HTML report with AI insights (`trading_report_with_llm.html`)
4. Provide AI-driven recommendations for improving your trading strategy

#### Setup for AI Analysis:

1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Add the following to your `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=openai/gpt-oss-120b:free
   ```

### Trading Plan Adherence Review

To evaluate how well your trades adhere to your trading plan:
```
python trading_plan_review.py
```

This tool:
1. Guides you through defining your trading plan parameters (first-time use)
2. Analyzes your trades against your defined plan
3. Calculates an adherence score for your trading discipline
4. Provides recommendations for improving plan compliance
5. Highlights whether profitable trades occur outside your plan parameters

## Analysis Features

### Performance Metrics

- **Overall Profitability**
  - Total PnL and daily breakdown
  - Gross profit and gross loss
  - Profit factor (gross profit / gross loss)
  - Maximum drawdown analysis

- **Trade Statistics**
  - Win/loss ratio and win rate percentage
  - Average profit vs. average loss
  - Reward-to-risk ratio
  - Consecutive wins/losses tracking

- **Symbol Analysis**
  - Performance by trading symbol/instrument
  - Win rate per symbol
  - Most profitable and least profitable symbols

- **Temporal Analysis**
  - Best and worst trading hours
  - Daily performance patterns
  - Trade duration analysis (how long you hold winning vs. losing trades)

### Visualization Tools

- **Cumulative PnL Chart**: Shows profit/loss evolution with drawdown visualization
- **PnL Distribution**: Histograms showing the distribution of your winning and losing trades
- **Time-Based Analysis**: Hour of day performance heatmap
- **Symbol Performance**: Comparative analysis of different symbols
- **Trade Duration Analysis**: Analysis of holding periods for profitable vs. unprofitable trades

### Recommendations Engine

The HTML report includes AI-driven recommendations based on your trading patterns:

- Identifying your best performing symbols
- Optimal trading hours based on historical performance
- Suggestions for trade duration management
- Areas for improvement in your trading strategy

## Security Note

Your API credentials are stored in the `.env` file, which should never be committed to version control.
The `.gitignore` file should include `.env` to prevent accidental exposure of your credentials.

## Troubleshooting

### SSL Certificate Verification Failed

If you encounter an error like:
```
SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'api.bybit.com'"))
```

This is caused by a mismatch between the hostname in the SSL certificate and the hostname being used to connect to the Bybit API.

To resolve this issue:

1. Set `DISABLE_SSL_VERIFY=true` in your `.env` file
2. Run the script again

**Note:** Disabling SSL verification reduces security and should only be used for testing purposes. In a production environment, consider using a properly configured SSL certificate.
