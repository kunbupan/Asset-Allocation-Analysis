# Multi-Asset Momentum: Backtest, Performance & Attribution

**Does a 12-month momentum rule beat a static 60/40 portfolio after costs, and if so, where does the difference come from?**

This project backtests a tactical asset-allocation strategy across seven ETFs, then evaluates it the way an asset manager's performance team would: risk-adjusted returns against a benchmark, and Brinson-Fachler attribution that splits the active return into asset-allocation, selection and cost effects.

> Personal research project. Not investment advice.

---

## Key findings

| | Momentum (net of costs) | 60/40 benchmark |
|---|---|---|
| CAGR | 7.92% | 8.16% |
| Volatility | 11.99% | 9.25% |
| Sharpe ratio | 0.49 | 0.67 |
| Max drawdown | −19.13% | −29.46% |
| Calmar ratio | 0.41 | 0.28 |
| Positive months | 57.26% | 66.94% |
| Avg monthly turnover | 27.02% | — |
| Months fully in cash | 2.81% | — |

*Period: March 2006 to October 2026 (248 months), monthly data.*

- The strategy lagged the 60/40 by 0.2% a year but cut the maximum drawdown from 29.5% to 19.1%.
- `[Attribution: e.g. "Most of the shortfall came from allocation: time spent in cash and real assets during the post-2009 equity rally."]`
- `[Robustness: e.g. "Results hold for lookbacks of 6–12 months but weaken for top-N above 3."]`

![Growth of $1 and drawdowns: momentum vs 60/40](reports/figures/growth_drawdown.png)
*Top: growth of $1 invested in March 2006 (log scale). Bottom: decline from the previous peak.*

---

## 1. Strategy and benchmark

| | |
|---|---|
| **Universe** | SPY (US equity), EFA (developed ex-US equity), EEM (emerging equity), IEF (7–10y Treasuries), TLT (20y+ Treasuries), GLD (gold), VNQ (US REITs) |
| **Signal** | 12-month total return, skipping the most recent month (short-term reversal) |
| **Portfolio** | Top 3 assets, equally weighted; an asset with negative momentum is replaced by cash (absolute momentum) |
| **Rebalancing** | Monthly, at month-end close |
| **Costs** | 10 bps one-way, charged on turnover |
| **Benchmark** | 60% SPY / 40% IEF, rebalanced monthly |

## 2. Data

- Monthly adjusted close prices from Yahoo Finance via `yfinance` (dividends reinvested).
- All data is public, so anyone can rerun the analysis with one command.

## 3. Methodology

**No look-ahead.** Signals use data up to month-end *t* and are applied to returns in month *t+1*.

**Performance metrics.** CAGR, annualised volatility, Sharpe and Sortino ratios, maximum drawdown, Calmar ratio, tracking error, information ratio, and rolling 36-month versions of the key ratios.

**Attribution: Brinson-Fachler by asset class.** Each month, the active return (portfolio minus benchmark) is split into:

| Effect | Formula | Question it answers |
|---|---|---|
| Allocation | (w<sub>p</sub> − w<sub>b</sub>) × (r<sub>b,i</sub> − R<sub>b</sub>) | Did over- or underweighting an asset class help? |
| Selection | w<sub>b</sub> × (r<sub>p,i</sub> − r<sub>b,i</sub>) | Did choosing different ETFs within a class help (e.g. TLT instead of IEF)? |
| Interaction | (w<sub>p</sub> − w<sub>b</sub>) × (r<sub>p,i</sub> − r<sub>b,i</sub>) | The combined effect of the two decisions |
| Trading costs | − turnover × cost | How much implementation cost |

Asset classes: Equity (SPY, EFA, EEM), Bonds (IEF, TLT), Real assets (GLD, VNQ) and Cash. The benchmark holds no real assets, so a 50/50 GLD/VNQ mix serves as the neutral return for that class.

Monthly effects are linked over time with the **Carino method**, so the linked effects add up exactly to the cumulative active return. The code checks this reconciliation on every run.

**Robustness.** A parameter sweep over lookback (3–12 months) and top-N (1–5), plus results by sub-period, to see whether the result depends on one lucky parameter choice or one market regime.

## 4. Results

### Attribution summary

<!-- Paste the summary table from notebooks/02_performance_attribution.ipynb -->

| Asset class | Allocation | Selection | Interaction | Total |
|---|---|---|---|---|
| Equity | | | | |
| Bonds | | | | |
| Real assets | | | | |
| Cash | | | | |
| Trading costs | | | | |
| **Total** | | | | |

![Attribution by year](reports/figures/attribution_by_year.png)

### Robustness

![Sharpe ratio across lookback and top-N](reports/figures/parameter_sweep.png)

`[2–3 sentences: what the sweep and sub-periods show.]`

### Dashboard

`[Link to Tableau Public / Power BI dashboard, with a screenshot]`

## 5. Limitations

- **Short, survivorship-biased history.** ETFs only go back to the early 2000s, and the universe contains funds that still exist today.
- **Idealised execution.** Fills at month-end close, flat 10 bps cost, no taxes.
- **One strategy family.** Momentum is well documented in the literature, so the edge, if any, may already be arbitraged away.
- **Attribution is by asset class**, not by security, and depends on the chosen class benchmarks (notably the GLD/VNQ proxy).

## 6. Project structure

```
├── notebooks/
│   ├── 01_backtest.ipynb                 # strategy, benchmark, headline statistics
│   └── 02_performance_attribution.ipynb  # metrics, attribution, robustness, charts
├── src/
│   ├── backtest.py                       # signal, weights, returns, costs
│   ├── performance.py                    # risk and return metrics
│   └── attribution.py                    # Brinson-Fachler + Carino linking
├── reports/figures/                      # charts used in this README
├── dashboard/                            # exported CSVs for Tableau / Power BI
└── requirements.txt
```

## 7. How to run

```bash
pip install -r requirements.txt
jupyter notebook notebooks/01_backtest.ipynb
```

Or open the notebooks directly in Google Colab.
