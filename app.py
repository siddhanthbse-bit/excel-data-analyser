import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Excel Data Analyser",
    page_icon="📊",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Background */
    .stApp { background-color: #0f1117; }

    /* Header banner */
    .hero {
        background: linear-gradient(135deg, #1a1f2e 0%, #16213e 60%, #0f3460 100%);
        border: 1px solid #2d3561;
        border-radius: 16px;
        padding: 2.5rem 2rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero h1 {
        font-size: 2.4rem;
        font-weight: 800;
        color: #e0e6f8;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .hero p {
        color: #8892b0;
        font-size: 1.05rem;
        margin-top: 0.5rem;
    }
    .accent { color: #64ffda; }

    /* Metric cards */
    .metric-card {
        background: #1a1f2e;
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.6rem;
    }
    .metric-card .label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #8892b0;
        margin-bottom: 0.3rem;
    }
    .metric-card .value {
        font-size: 1.55rem;
        font-weight: 700;
        color: #ccd6f6;
    }

    /* Forecast badge */
    .badge-yes {
        background: #003d2e;
        color: #64ffda;
        border: 1px solid #64ffda;
        border-radius: 20px;
        padding: 0.25rem 0.85rem;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-no {
        background: #3d1a00;
        color: #ff9e64;
        border: 1px solid #ff9e64;
        border-radius: 20px;
        padding: 0.25rem 0.85rem;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Section heading */
    .section-head {
        font-size: 1.15rem;
        font-weight: 700;
        color: #ccd6f6;
        border-left: 3px solid #64ffda;
        padding-left: 0.75rem;
        margin: 1.8rem 0 1rem;
    }

    /* Upload area */
    [data-testid="stFileUploader"] {
        background: #1a1f2e;
        border: 2px dashed #2d3561;
        border-radius: 12px;
        padding: 1rem;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #64ffda;
    }

    /* Divider */
    hr { border-color: #2d3561; margin: 2rem 0; }

    /* Hide default streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>📊 Excel Data <span class="accent">Analyser</span></h1>
  <p>Upload any Excel file · Auto-detect numeric columns · Histograms · Forecasting readiness check</p>
</div>
""", unsafe_allow_html=True)

# ── File upload ───────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drop your Excel file here (.xlsx or .xls)",
    type=["xlsx", "xls"],
)

# ── Threshold slider ──────────────────────────────────────────────────────────
with st.expander("⚙️  Adjust forecasting threshold", expanded=False):
    threshold = st.slider(
        "Max allowed % difference between Mean & Median",
        min_value=1, max_value=30, value=10, step=1,
        help="If |(mean−median)/mean| × 100 ≤ threshold → data is suitable for forecasting."
    )

# ── Main logic ────────────────────────────────────────────────────────────────
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Could not read the file: {e}")
        st.stop()

    st.markdown('<div class="section-head">Preview — first 5 rows</div>', unsafe_allow_html=True)
    st.dataframe(df.head(), use_container_width=True)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        st.warning("No numeric columns found in this file.")
        st.stop()

    st.markdown(
        f'<div class="section-head">Found {len(numeric_cols)} numeric column(s)</div>',
        unsafe_allow_html=True,
    )

    # ── Summary table ─────────────────────────────────────────────────────────
    summary_rows = []
    for col in numeric_cols:
        series = df[col].dropna()
        mean_val = series.mean()
        median_val = series.median()
        pct_diff = abs(mean_val - median_val) / abs(mean_val) * 100 if mean_val != 0 else 0
        forecast_ok = pct_diff <= threshold
        summary_rows.append({
            "Column": col,
            "Count": len(series),
            "Mean": round(mean_val, 4),
            "Median": round(median_val, 4),
            "% Diff": round(pct_diff, 2),
            "Forecast Ready": "✅ Yes" if forecast_ok else "❌ No",
        })

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # ── Histograms ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-head">Histograms with Mean & Median</div>', unsafe_allow_html=True)

    plt.style.use("dark_background")

    for i in range(0, len(numeric_cols), 2):
        cols_in_row = numeric_cols[i: i + 2]
        grid = st.columns(len(cols_in_row))

        for j, col in enumerate(cols_in_row):
            series = df[col].dropna()
            mean_val = series.mean()
            median_val = series.median()
            pct_diff = abs(mean_val - median_val) / abs(mean_val) * 100 if mean_val != 0 else 0
            forecast_ok = pct_diff <= threshold

            fig, ax = plt.subplots(figsize=(6, 3.8))
            fig.patch.set_facecolor("#1a1f2e")
            ax.set_facecolor("#0f1117")

            n, bins, patches = ax.hist(
                series, bins="auto",
                color="#3a5fc8", edgecolor="#0f1117", linewidth=0.4, alpha=0.85,
            )

            ax.axvline(mean_val, color="#64ffda", linewidth=1.8, linestyle="--", label=f"Mean: {mean_val:.2f}")
            ax.axvline(median_val, color="#ff9e64", linewidth=1.8, linestyle="-.",  label=f"Median: {median_val:.2f}")

            ax.set_title(col, fontsize=11, fontweight="bold", color="#ccd6f6", pad=8)
            ax.set_xlabel("Value", fontsize=8, color="#8892b0")
            ax.set_ylabel("Frequency", fontsize=8, color="#8892b0")
            ax.tick_params(colors="#8892b0", labelsize=7)
            for spine in ax.spines.values():
                spine.set_edgecolor("#2d3561")

            legend = ax.legend(fontsize=7.5, facecolor="#1a1f2e", edgecolor="#2d3561", labelcolor="#ccd6f6")

            verdict = f"✅ Forecast Ready  (Δ {pct_diff:.1f}%)" if forecast_ok else f"❌ Skewed  (Δ {pct_diff:.1f}%)"
            verdict_color = "#64ffda" if forecast_ok else "#ff9e64"
            ax.text(
                0.98, 0.97, verdict,
                transform=ax.transAxes, fontsize=7.5,
                color=verdict_color, ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#0f1117", edgecolor=verdict_color, alpha=0.9),
            )

            fig.tight_layout()

            with grid[j]:
                st.pyplot(fig)
                plt.close(fig)

                # Per-column metric cards
                st.markdown(f"""
                <div class="metric-card">
                  <div class="label">Mean</div>
                  <div class="value">{mean_val:,.4f}</div>
                </div>
                <div class="metric-card">
                  <div class="label">Median</div>
                  <div class="value">{median_val:,.4f}</div>
                </div>
                <div class="metric-card">
                  <div class="label">Forecasting Suitability</div>
                  <div class="value" style="font-size:1rem; margin-top:0.3rem;">
                    {"<span class='badge-yes'>✅ Suitable</span>" if forecast_ok else "<span class='badge-no'>❌ Skewed data</span>"}
                    &nbsp; <span style="color:#8892b0; font-size:0.8rem;">Δ {pct_diff:.1f}% (threshold {threshold}%)</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-head">How the forecasting check works</div>', unsafe_allow_html=True)
    st.markdown("""
A column is marked **Forecast Ready** when:

```
| mean − median |
─────────────────  ×  100  ≤  threshold %
      | mean |
```

When mean ≈ median the distribution is roughly symmetric (close to normal), which is a good prerequisite for most time-series and regression forecasting methods.  
You can adjust the threshold in the settings panel above.
""")

else:
    st.info("👆 Upload an Excel file to get started.")
