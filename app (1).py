import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Excel Data Analyser", page_icon="📊", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0f1117; }
.hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f3460 100%);
    border: 1px solid #2d3561;
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
}
.hero h1 { font-size: 2.2rem; font-weight: 800; color: #e0e6f8; margin: 0; }
.hero p { color: #8892b0; font-size: 1rem; margin-top: 0.5rem; }
.accent { color: #64ffda; }
.section-head {
    font-size: 1.1rem; font-weight: 700; color: #ccd6f6;
    border-left: 3px solid #64ffda;
    padding-left: 0.75rem; margin: 1.8rem 0 1rem;
}
.metric-card {
    background: #1a1f2e; border: 1px solid #2d3561;
    border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;
}
.metric-card .label { font-size: 0.75rem; text-transform: uppercase;
    letter-spacing: 1.5px; color: #8892b0; margin-bottom: 0.2rem; }
.metric-card .value { font-size: 1.4rem; font-weight: 700; color: #ccd6f6; }
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>📊 Excel Data <span class="accent">Analyser</span></h1>
  <p>Upload any Excel file · Auto-detect numeric columns · Histograms · Forecasting readiness check</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Drop your Excel file here (.xlsx or .xls)", type=["xlsx", "xls"])

with st.expander("⚙️ Adjust forecasting threshold", expanded=False):
    threshold = st.slider(
        "Max allowed % difference between Mean & Median",
        min_value=1, max_value=30, value=10, step=1
    )

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception:
        try:
            df = pd.read_excel(uploaded_file, engine="xlrd")
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

    st.markdown('<div class="section-head">Preview — first 5 rows</div>', unsafe_allow_html=True)
    st.dataframe(df.head(), use_container_width=True)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        st.warning("No numeric columns found in this file.")
        st.stop()

    st.markdown(f'<div class="section-head">Found {len(numeric_cols)} numeric column(s)</div>', unsafe_allow_html=True)

    # Summary table
    rows = []
    for col in numeric_cols:
        s = df[col].dropna()
        mean_v = s.mean()
        median_v = s.median()
        pct = abs(mean_v - median_v) / abs(mean_v) * 100 if mean_v != 0 else 0
        rows.append({
            "Column": col,
            "Count": len(s),
            "Mean": round(mean_v, 4),
            "Median": round(median_v, 4),
            "% Diff": round(pct, 2),
            "Forecast Ready": "✅ Yes" if pct <= threshold else "❌ No",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-head">Histograms with Mean & Median</div>', unsafe_allow_html=True)

    for i in range(0, len(numeric_cols), 2):
        chunk = numeric_cols[i:i+2]
        cols = st.columns(len(chunk))

        for j, col in enumerate(chunk):
            s = df[col].dropna()
            mean_v = s.mean()
            median_v = s.median()
            pct = abs(mean_v - median_v) / abs(mean_v) * 100 if mean_v != 0 else 0
            ok = pct <= threshold

            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=s, name=col,
                marker_color="#3a5fc8", opacity=0.85,
                nbinsx=30
            ))
            fig.add_vline(x=mean_v, line_dash="dash", line_color="#64ffda", line_width=2,
                          annotation_text=f"Mean: {mean_v:.2f}", annotation_font_color="#64ffda",
                          annotation_position="top right")
            fig.add_vline(x=median_v, line_dash="dot", line_color="#ff9e64", line_width=2,
                          annotation_text=f"Median: {median_v:.2f}", annotation_font_color="#ff9e64",
                          annotation_position="top left")

            verdict = f"✅ Forecast Ready  (Δ {pct:.1f}%)" if ok else f"❌ Skewed  (Δ {pct:.1f}%)"
            fig.add_annotation(
                text=verdict,
                xref="paper", yref="paper", x=0.99, y=0.97,
                showarrow=False,
                font=dict(color="#64ffda" if ok else "#ff9e64", size=11),
                bgcolor="#0f1117", bordercolor="#64ffda" if ok else "#ff9e64",
                borderwidth=1, borderpad=5, align="right"
            )

            fig.update_layout(
                title=dict(text=col, font=dict(color="#ccd6f6", size=14)),
                paper_bgcolor="#1a1f2e", plot_bgcolor="#0f1117",
                font=dict(color="#8892b0"),
                xaxis=dict(gridcolor="#2d3561", zerolinecolor="#2d3561"),
                yaxis=dict(gridcolor="#2d3561", zerolinecolor="#2d3561"),
                margin=dict(t=50, b=30, l=30, r=30),
                showlegend=False, height=320,
            )

            with cols[j]:
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(f"""
                <div class="metric-card"><div class="label">Mean</div><div class="value">{mean_v:,.4f}</div></div>
                <div class="metric-card"><div class="label">Median</div><div class="value">{median_v:,.4f}</div></div>
                <div class="metric-card">
                  <div class="label">Forecasting Suitability</div>
                  <div class="value" style="font-size:0.95rem; margin-top:0.3rem;">
                    {"✅ Suitable" if ok else "❌ Skewed data"} &nbsp;
                    <span style="color:#8892b0; font-size:0.78rem;">Δ {pct:.1f}% (threshold {threshold}%)</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-head">How the forecasting check works</div>', unsafe_allow_html=True)
    st.markdown("""
A column is marked **Forecast Ready** when:

```
| mean − median |  ×  100  ≤  threshold %
     | mean |
```

When mean ≈ median the distribution is roughly **symmetric**, which is a good sign for most forecasting methods (ARIMA, regression, exponential smoothing).  
Adjust the threshold in the settings panel above.
""")

else:
    st.info("👆 Upload an Excel file to get started.")
