"""
Brinson-Fachler performance attribution for a multi-asset portfolio.

Explains the portfolio's active return (portfolio minus benchmark) by
asset class, split into three effects:

    Allocation   (w_p - w_b) * (r_b,i - R_b)   over/underweighting a class
    Selection     w_b * (r_p,i - r_b,i)        picking different assets inside a class
    Interaction  (w_p - w_b) * (r_p,i - r_b,i) the combination of the two

Single-period effects add up exactly to the monthly active return. Monthly
effects are linked over time with the Carino (1999) method, so that the
linked effects add up to the *cumulative* active return.

Conventions
-----------
- Weights decided at month-end t earn the returns of month t+1 (pass the
  weights already shifted, i.e. the weights actually held).
- Any weight not invested is cash. Cash is its own asset class.
- When the portfolio holds nothing in a class, its class return is set to
  the benchmark class return, so it creates no selection effect.
- When the benchmark holds nothing in a class (e.g. gold in a 60/40), a
  neutral proxy return is needed for that class: see `class_benchmarks`.
"""

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Asset-class set-up (edit to match the universe)
# ----------------------------------------------------------------------------

ASSET_CLASSES = {
    "SPY": "Equity", "EFA": "Equity", "EEM": "Equity",
    "IEF": "Bonds",  "TLT": "Bonds",
    "GLD": "Real assets", "VNQ": "Real assets",
}

# Return used as the benchmark return for each class. A class the benchmark
# does not hold still needs a neutral return, otherwise allocation into it
# cannot be measured.
CLASS_BENCHMARKS = {
    "Equity": {"SPY": 1.0},
    "Bonds": {"IEF": 1.0},
    "Real assets": {"GLD": 0.5, "VNQ": 0.5},
}

CASH = "Cash"


# ----------------------------------------------------------------------------
# Building blocks
# ----------------------------------------------------------------------------

def class_weights(weights, classes=ASSET_CLASSES):
    """Asset weights -> asset-class weights, with uninvested weight as cash."""
    by_class = weights.T.groupby(classes).sum().T
    by_class[CASH] = 1.0 - by_class.sum(axis=1)
    return by_class


def class_returns(weights, returns, classes=ASSET_CLASSES, fallback=None,
                  cash_return=0.0):
    """Weighted return of each class's holdings; `fallback` where none held."""
    contrib = (weights * returns).T.groupby(classes).sum().T
    w = weights.T.groupby(classes).sum().T
    r = contrib / w.where(w > 0)            # NaN where nothing is held
    if fallback is not None:
        r = r.fillna(fallback[r.columns])
    r[CASH] = cash_return
    return r


def benchmark_class_returns(returns, class_benchmarks=CLASS_BENCHMARKS,
                            cash_return=0.0):
    """Neutral return per class, from the CLASS_BENCHMARKS mix."""
    out = {}
    for cls, mix in class_benchmarks.items():
        w = pd.Series(mix)
        out[cls] = (returns[w.index] * w).sum(axis=1)
    out = pd.DataFrame(out)
    out[CASH] = cash_return
    return out


# ----------------------------------------------------------------------------
# Attribution
# ----------------------------------------------------------------------------

def brinson_fachler(wp, wb, rp, rb):
    """
    Single-period effects for every period (rows) and class (columns).

    wp, wb : portfolio / benchmark class weights (rows sum to 1)
    rp, rb : portfolio / benchmark class returns
    Returns a DataFrame with a (effect, class) column MultiIndex.
    """
    Rb = (wb * rb).sum(axis=1)

    allocation = (wp - wb) * rb.sub(Rb, axis=0)
    selection = wb * (rp - rb)
    interaction = (wp - wb) * (rp - rb)

    return pd.concat({"Allocation": allocation,
                      "Selection": selection,
                      "Interaction": interaction}, axis=1)


def carino_link(effects, port_ret, bench_ret):
    """
    Link monthly effects so they sum to the cumulative active return.

    k_t = ln(1+R_t) - ln(1+B_t) / (R_t - B_t)   (per period)
    K   = same formula on cumulative returns
    linked effect = sum_t( effect_t * k_t / K )
    """
    def k(r, b):
        diff = r - b
        same = np.isclose(diff, 0)
        safe = np.where(same, 1.0, diff)
        return np.where(same, 1 / (1 + r), (np.log1p(r) - np.log1p(b)) / safe)

    R = (1 + port_ret).prod() - 1
    B = (1 + bench_ret).prod() - 1
    k_t = pd.Series(k(port_ret.values, bench_ret.values), index=port_ret.index)
    K = float(k(np.array([R]), np.array([B]))[0])

    return effects.mul(k_t / K, axis=0).sum()


def attribution_report(held_weights, bench_weights, returns, costs=None,
                       cash_return=0.0, classes=ASSET_CLASSES,
                       class_benchmarks=CLASS_BENCHMARKS):
    """
    Full multi-period attribution.

    held_weights  : weights actually held each month (already shifted)
    bench_weights : benchmark asset weights each month (same shape)
    returns       : monthly asset returns
    costs         : monthly trading costs as a return drag (optional)

    Returns (summary table by class, monthly effects, check dict).
    """
    rb_cls_neutral = benchmark_class_returns(returns, class_benchmarks,
                                             cash_return)

    wp = class_weights(held_weights, classes)
    wb = class_weights(bench_weights, classes)
    rp = class_returns(held_weights, returns, classes, rb_cls_neutral,
                       cash_return)
    rb = class_returns(bench_weights, returns, classes, rb_cls_neutral,
                       cash_return)

    cols = wp.columns
    wb, rp, rb = wb[cols], rp[cols], rb[cols]

    port_gross = (wp * rp).sum(axis=1)
    bench = (wb * rb).sum(axis=1)
    port_net = port_gross - (costs if costs is not None else 0.0)

    effects = brinson_fachler(wp, wb, rp, rb)
    if costs is not None:
        effects[("Trading costs", "Total")] = -costs

    linked = carino_link(effects, port_net, bench)
    summary = linked.unstack(level=0).fillna(0.0)
    summary["Total"] = summary.sum(axis=1)
    summary.loc["Total"] = summary.sum()

    check = {
        "cumulative portfolio": (1 + port_net).prod() - 1,
        "cumulative benchmark": (1 + bench).prod() - 1,
        "active return": (1 + port_net).prod() - (1 + bench).prod(),
        "sum of linked effects": summary.loc["Total", "Total"],
    }
    return summary, effects, check
