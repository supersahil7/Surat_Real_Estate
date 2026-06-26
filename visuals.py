import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Surat Real Estate Analytics",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base & font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #0f2027 0%, #1a3a4a 60%, #203a43 100%);
    border-right: 1px solid #2a5568;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 0.95rem; padding: 6px 0; }

/* ── KPI card ── */
.kpi-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #1a2d45 100%);
    border: 1px solid #2d5986;
    border-radius: 12px;
    padding: 18px 22px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}
.kpi-label {
    color: #94b8d8;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.kpi-value {
    color: #e8f4fd;
    font-size: 1.75rem;
    font-weight: 700;
    font-family: 'Playfair Display', serif;
    line-height: 1.2;
}
.kpi-sub {
    color: #64a0c8;
    font-size: 0.72rem;
    margin-top: 4px;
}

/* ── Section header ── */
.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem;
    color: #1a3a4a;
    border-bottom: 3px solid #10b981;
    padding-bottom: 6px;
    margin: 22px 0 14px 0;
}

/* ── Chart card ── */
.chart-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 8px;
    border: 1px solid #e5f0f8;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

/* ── Page title ── */
.page-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.1rem;
    color: #0f2027;
    font-weight: 700;
    line-height: 1.1;
}
.page-subtitle {
    color: #547a8c;
    font-size: 0.95rem;
    margin-top: 2px;
    margin-bottom: 24px;
}

/* ── Insight box ── */
.insight-box {
    background: linear-gradient(90deg, #ecfdf5 0%, #f0fdfb 100%);
    border-left: 4px solid #10b981;
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    font-size: 0.87rem;
    color: #064e3b;
    margin-top: 8px;
}

/* ── Property finder table ── */
.stDataFrame { border-radius: 10px !important; }

/* ── SQL code blocks ── */
.sql-block { border-radius: 10px; margin-bottom: 18px; }
.sql-title {
    font-weight: 600;
    font-size: 1rem;
    color: #1a3a4a;
    margin-bottom: 6px;
}

/* ── Footer ── */
.footer-bar {
    text-align: center;
    color: #94a3b8;
    font-size: 0.75rem;
    padding: 18px 0 4px 0;
    border-top: 1px solid #e2e8f0;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("surti_clean_set2.csv", on_bad_lines="skip")

    for col in ["sale_price", "sqft_numeric", "price_per_sqft_numeric"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Property category (from property_name) ──
    def extract_category(name):
        if pd.isna(name):
            return "Unknown"
        name = name.strip()
        m = re.search(
            r"^(\d+\s*BHK|House|Land|Office Space|Shop|Showroom|"
            r"Industrial|Warehouse|Villa|Flat|Plot|Commercial)",
            name, re.IGNORECASE,
        )
        return m.group(1).strip() if m else "Other"

    df["category"] = df["property_name"].apply(extract_category)

    # ── Floor bucket ──
    def floor_bucket(f):
        if pd.isna(f):
            return None
        if str(f).strip().lower() == "ground":
            return "Ground"
        try:
            num = int(str(f).split(" out of ")[0])
            if num <= 3:
                return "Low (1–3)"
            elif num <= 8:
                return "Mid (4–8)"
            else:
                return "High (9+)"
        except Exception:
            return None

    df["floor_bucket"] = df["floor"].apply(floor_bucket)

    # ── Luxury segment ──
    def segment(p):
        if pd.isna(p):
            return None
        if p < 5_000_000:
            return "Budget (<50L)"
        elif p < 10_000_000:
            return "Mid-Range (50L–1Cr)"
        elif p < 20_000_000:
            return "Premium (1Cr–2Cr)"
        else:
            return "Luxury (>2Cr)"

    df["segment"] = df["sale_price"].apply(segment)

    # ── Price in lakhs ──
    df["price_lakh"] = df["sale_price"] / 1e5

    return df


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
EMERALD = "#10b981"
PALETTE = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
           "#06b6d4", "#ec4899", "#84cc16"]
SEG_COLORS = {
    "Budget (<50L)":       "#3b82f6",
    "Mid-Range (50L–1Cr)": "#10b981",
    "Premium (1Cr–2Cr)":   "#f59e0b",
    "Luxury (>2Cr)":       "#ef4444",
}
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#334155"),
    margin=dict(l=10, r=10, t=40, b=10),
    title_font=dict(size=14, color="#1a3a4a", family="Inter, sans-serif"),
)
# Default legend style applied per-chart to avoid duplicate-kwarg conflicts
_LEGEND = dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)")


def fmt_lakh(val):
    if val >= 100:
        return f"₹{val/100:.2f} Cr"
    return f"₹{val:.1f} L"


def kpi(label, value, sub=""):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""


def insight(text):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 8px 0 18px 0;'>
        <div style='font-size:2.2rem;'>🏙️</div>
        <div style='font-family:"Playfair Display",serif; font-size:1.1rem;
                    color:#e2e8f0; font-weight:700; margin-top:4px;'>
            Surat Realty
        </div>
        <div style='color:#64a0c8; font-size:0.75rem; margin-top:2px;'>
            Analytics Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["📈 Executive Overview",
         "💡 Buyer Insights",
         "🔍 Property Finder",
         "💻 SQL Showcase"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        "<div style='color:#64a0c8; font-size:0.73rem; padding:4px 0;'>"
        "Dataset: <b style='color:#94b8d8;'>surti_clean_set2.csv</b><br>"
        "Records: <b style='color:#94b8d8;'>~4,415</b> | Columns: <b style='color:#94b8d8;'>16</b><br>"
        "Source: Surat Housing Listings"
        "</div>",
        unsafe_allow_html=True,
    )

df = load_data()


# ═════════════════════════════════════════════════════════════════
# PAGE 1 – EXECUTIVE OVERVIEW
# ═════════════════════════════════════════════════════════════════
if page == "📈 Executive Overview":
    st.markdown('<div class="page-title">Executive Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Macro market analysis of the Surat residential & commercial real estate landscape</div>', unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────
    total       = len(df)
    med_lakh    = df["price_lakh"].median()
    avg_cr      = df["sale_price"].mean() / 1e7
    avg_psf     = df["price_per_sqft_numeric"].mean()
    med_psf     = df["price_per_sqft_numeric"].median()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(kpi("Total Properties", f"{total:,}", "Active listings"), unsafe_allow_html=True)
    c2.markdown(kpi("Median Price", fmt_lakh(med_lakh), "50th percentile"), unsafe_allow_html=True)
    c3.markdown(kpi("Avg Price", f"₹{avg_cr:.2f} Cr", "Mean across all types"), unsafe_allow_html=True)
    c4.markdown(kpi("Avg Price/Sqft", f"₹{avg_psf:,.0f}", "Per sq. ft."), unsafe_allow_html=True)
    c5.markdown(kpi("Median Price/Sqft", f"₹{med_psf:,.0f}", "50th percentile"), unsafe_allow_html=True)

    st.markdown("")

    # ── Row 1: Pie + Scatter ───────────────────────────────────────
    col_a, col_b = st.columns([1, 1.6])

    with col_a:
        st.markdown('<div class="section-header">Luxury Segmentation</div>', unsafe_allow_html=True)
        seg_df = df["segment"].dropna().value_counts().reset_index()
        seg_df.columns = ["Segment", "Count"]
        seg_order = ["Budget (<50L)", "Mid-Range (50L–1Cr)", "Premium (1Cr–2Cr)", "Luxury (>2Cr)"]
        seg_df["Segment"] = pd.Categorical(seg_df["Segment"], categories=seg_order, ordered=True)
        seg_df = seg_df.sort_values("Segment")
        seg_df["Share"] = (seg_df["Count"] / seg_df["Count"].sum() * 100).round(1)

        fig_pie = px.pie(
            seg_df, names="Segment", values="Count",
            color="Segment", color_discrete_map=SEG_COLORS,
            hole=0.52,
            custom_data=["Share"],
        )
        fig_pie.update_traces(
            hovertemplate="<b>%{label}</b><br>%{value:,} properties (%{customdata[0]:.1f}%)<extra></extra>",
            textposition="outside",
            textfont_size=11,
        )
        fig_pie.update_layout(
            **PLOTLY_LAYOUT,
            title="Market Composition by Price Band",
            showlegend=True,
            legend=dict(orientation="v", x=0.01, y=0.5, font=dict(size=10)),
            annotations=[dict(text=f"<b>{total:,}</b><br>listings", x=0.5, y=0.5,
                              font_size=12, showarrow=False, font_color="#1a3a4a")],
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        insight("Surat is primarily a mid-market city. Budget + Mid-Range together account for ~65% of listings, yet a robust 18% luxury segment signals strong premium demand.")

    with col_b:
        st.markdown('<div class="section-header">Property Size vs Price</div>', unsafe_allow_html=True)
        scatter_df = df[
            df["sqft_numeric"].notna() &
            df["sale_price"].notna() &
            (df["sqft_numeric"] <= 10_000)
        ].copy()
        scatter_df["price_cr"] = scatter_df["sale_price"] / 1e7
        scatter_df["Segment"] = scatter_df["segment"].fillna("Unknown")

        fig_sc = px.scatter(
            scatter_df, x="sqft_numeric", y="price_cr",
            color="Segment", color_discrete_map=SEG_COLORS,
            opacity=0.55, size_max=8,
            labels={"sqft_numeric": "Area (sq. ft.)", "price_cr": "Price (₹ Cr)"},
            hover_data={"sqft_numeric": True, "price_cr": ":.2f", "Segment": True},
        )
        fig_sc.update_traces(marker=dict(size=5))
        fig_sc.update_layout(
            **PLOTLY_LAYOUT,
            legend=_LEGEND,
            title="Valuation Distribution – Size vs Price (≤10,000 sqft)",
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat=","),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        )
        st.plotly_chart(fig_sc, use_container_width=True)
        insight("A clear positive correlation exists between size and price. Premium outliers appear even in smaller properties, pointing to location-driven valuation.")

    # ── Row 2: Top 8 Property Categories by Median Price ─────────
    st.markdown('<div class="section-header">Median Price by Property Category</div>', unsafe_allow_html=True)

    cat_price = (
        df[df["sale_price"].notna()]
        .groupby("category")["price_lakh"]
        .median()
        .reset_index()
        .rename(columns={"price_lakh": "Median Price (L)"})
        .sort_values("Median Price (L)", ascending=False)
        .head(12)
    )
    cat_price["Price Label"] = cat_price["Median Price (L)"].apply(fmt_lakh)

    fig_bar = px.bar(
        cat_price, x="Median Price (L)", y="category",
        orientation="h", text="Price Label",
        color="Median Price (L)",
        color_continuous_scale=["#bfdbfe", "#3b82f6", "#1d4ed8"],
        labels={"category": "", "Median Price (L)": "Median Price (Lakhs)"},
    )
    fig_bar.update_traces(textposition="outside", textfont_size=11)
    fig_bar.update_layout(
        **PLOTLY_LAYOUT,
        legend=_LEGEND,
        title="Median Price by Property Type",
        yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
        coloraxis_showscale=False,
        height=380,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    insight("Luxury residential (5+ BHK, 6 BHK) and commercial categories (Showroom, Office Space) command the highest median prices, reflecting demand at both ends of the spectrum.")


# ═════════════════════════════════════════════════════════════════
# PAGE 2 – BUYER INSIGHTS
# ═════════════════════════════════════════════════════════════════
elif page == "💡 Buyer Insights":
    st.markdown('<div class="page-title">Buyer Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Behavioural analysis across facing direction, area type, transaction type, and floor level</div>', unsafe_allow_html=True)

    # ── Chart 1 & 2: Facing + Area Type ──────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Facing Direction vs Median Price</div>', unsafe_allow_html=True)

        facing_df = (
            df[df["facing"].notna() & df["sale_price"].notna()]
            .groupby("facing")["price_lakh"]
            .median()
            .reset_index()
            .rename(columns={"price_lakh": "Median Price (L)"})
            .sort_values("Median Price (L)", ascending=False)
        )
        facing_df["Label"] = facing_df["Median Price (L)"].apply(fmt_lakh)

        VASTU_GOOD = {"North", "North-East", "East"}
        facing_df["Vastu"] = facing_df["facing"].apply(
            lambda x: "Vastu-Preferred" if x in VASTU_GOOD else "Other"
        )

        fig_facing = px.bar(
            facing_df, x="facing", y="Median Price (L)",
            color="Vastu",
            color_discrete_map={"Vastu-Preferred": EMERALD, "Other": "#64748b"},
            text="Label",
            labels={"facing": "Facing Direction", "Median Price (L)": "Median Price (₹ L)"},
        )
        fig_facing.update_traces(textposition="outside", textfont_size=10)
        fig_facing.update_layout(
            **PLOTLY_LAYOUT,
            title="Vastu Alignment Impact on Median Price",
            showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)"),
            xaxis=dict(tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            bargap=0.35,
        )
        st.plotly_chart(fig_facing, use_container_width=True)
        insight("North-East and North-facing properties fetch a premium, partially aligning with Vastu preferences. South-West commands the highest median — a location-driven anomaly.")

    with col2:
        st.markdown('<div class="section-header">Area Type vs Median Price/Sqft</div>', unsafe_allow_html=True)

        area_df = (
            df[df["areaWithType"].notna() & df["price_per_sqft_numeric"].notna()]
            .groupby("areaWithType")["price_per_sqft_numeric"]
            .median()
            .reset_index()
            .rename(columns={"price_per_sqft_numeric": "Median ₹/sqft"})
            .sort_values("Median ₹/sqft", ascending=False)
        )
        area_df["Label"] = area_df["Median ₹/sqft"].apply(lambda x: f"₹{x:,.0f}")

        fig_area = px.bar(
            area_df, x="areaWithType", y="Median ₹/sqft",
            color="Median ₹/sqft",
            color_continuous_scale=["#fef3c7", "#f59e0b", "#b45309"],
            text="Label",
            labels={"areaWithType": "Area Type", "Median ₹/sqft": "Median Price/Sqft (₹)"},
        )
        fig_area.update_traces(textposition="outside", textfont_size=11)
        fig_area.update_layout(
            **PLOTLY_LAYOUT,
            legend=_LEGEND,
            title="Pricing Premium by Area Type",
            coloraxis_showscale=False,
            xaxis=dict(tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            bargap=0.4,
        )
        st.plotly_chart(fig_area, use_container_width=True)
        insight("Plot Area commands the highest per-sqft premium (₹6,481), driven by land scarcity. Built Area is priced lowest — likely older construction or peripheral locations.")

    # ── Chart 3 & 4: Transaction Box Plot + Floor ─────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<div class="section-header">New Property vs Resale Prices</div>', unsafe_allow_html=True)

        txn_df = df[df["transaction"].notna() & df["sale_price"].notna()].copy()
        txn_df["Price (₹ Cr)"] = txn_df["sale_price"] / 1e7
        # Cap at 95th percentile per group for readability
        cap = txn_df.groupby("transaction")["Price (₹ Cr)"].quantile(0.95)
        txn_df = txn_df[
            txn_df.apply(lambda r: r["Price (₹ Cr)"] <= cap[r["transaction"]], axis=1)
        ]

        fig_box = px.box(
            txn_df, x="transaction", y="Price (₹ Cr)",
            color="transaction",
            color_discrete_map={"New Property": EMERALD, "Resale": "#3b82f6"},
            points="outliers",
            labels={"transaction": "Transaction Type", "Price (₹ Cr)": "Price (₹ Crores)"},
            notched=True,
        )
        fig_box.update_layout(
            **PLOTLY_LAYOUT,
            legend=_LEGEND,
            title="Price Distribution – New Launch vs Resale",
            showlegend=False,
            xaxis=dict(tickfont=dict(size=12)),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        )
        st.plotly_chart(fig_box, use_container_width=True)
        insight("New properties carry almost double the median price of resale listings (₹1.065 Cr vs ₹55L). The notched boxes confirm this difference is statistically meaningful.")

    with col4:
        st.markdown('<div class="section-header">Floor Level vs Median Price</div>', unsafe_allow_html=True)

        floor_df = (
            df[df["floor_bucket"].notna() & df["sale_price"].notna()]
            .groupby("floor_bucket")["price_lakh"]
            .median()
            .reset_index()
            .rename(columns={"price_lakh": "Median Price (L)"})
        )
        floor_order = ["Ground", "Low (1–3)", "Mid (4–8)", "High (9+)"]
        floor_df["floor_bucket"] = pd.Categorical(
            floor_df["floor_bucket"], categories=floor_order, ordered=True
        )
        floor_df = floor_df.sort_values("floor_bucket")
        floor_df["Label"] = floor_df["Median Price (L)"].apply(fmt_lakh)

        fig_floor = px.bar(
            floor_df, x="floor_bucket", y="Median Price (L)",
            color="Median Price (L)",
            color_continuous_scale=["#dbeafe", "#6366f1", "#3730a3"],
            text="Label",
            labels={"floor_bucket": "Floor Level", "Median Price (L)": "Median Price (₹ L)"},
        )
        fig_floor.update_traces(textposition="outside", textfont_size=11)
        fig_floor.update_layout(
            **PLOTLY_LAYOUT,
            legend=_LEGEND,
            title="Elevation Premium – Price by Floor Level",
            coloraxis_showscale=False,
            xaxis=dict(tickfont=dict(size=12)),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            bargap=0.38,
        )
        st.plotly_chart(fig_floor, use_container_width=True)
        insight("Mid-floor units fetch the highest median price (₹78L), outperforming even high-floor units. Ground floor is cheapest — buyers value elevation but not extreme heights.")

    # ── Chart 5: Furnishing Status vs Median Price ─────────────────
    st.markdown('<div class="section-header">Furnishing Status vs Median Price</div>', unsafe_allow_html=True)

    furn_df = (
        df[df["furnishing"].notna() & df["sale_price"].notna()]
        .groupby("furnishing")["price_lakh"]
        .median()
        .reset_index()
        .rename(columns={"price_lakh": "Median Price (L)"})
        .sort_values("Median Price (L)", ascending=False)
    )
    furn_df["Label"] = furn_df["Median Price (L)"].apply(fmt_lakh)
    furn_df["Count"] = furn_df["furnishing"].map(
        df[df["furnishing"].notna()].groupby("furnishing").size()
    )

    fig_furn = px.bar(
        furn_df, x="furnishing", y="Median Price (L)",
        color="furnishing",
        color_discrete_map={
            "Unfurnished": "#64748b", "Semi-Furnished": "#f59e0b", "Furnished": "#10b981"
        },
        text="Label",
        labels={"furnishing": "Furnishing Status", "Median Price (L)": "Median Price (₹ L)"},
    )
    fig_furn.update_traces(textposition="outside", textfont_size=12)
    fig_furn.update_layout(
        **PLOTLY_LAYOUT,
        legend=_LEGEND,
        title="Does Furnishing Command a Premium? — Median Price by Status",
        showlegend=False,
        xaxis=dict(tickfont=dict(size=13)),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        bargap=0.45,
        height=340,
    )
    st.plotly_chart(fig_furn, use_container_width=True)
    insight("Unfurnished properties carry the highest median price — counterintuitive at first glance, but reflects that larger, costlier properties (plots, villas) are often sold unfurnished. Location and size trump fittings.")


# ═════════════════════════════════════════════════════════════════
# PAGE 3 – PROPERTY FINDER
# ═════════════════════════════════════════════════════════════════
elif page == "🔍 Property Finder":
    st.markdown('<div class="page-title">Property Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Filter by your exact requirements and discover matching properties in Surat</div>', unsafe_allow_html=True)

    # ── Sidebar Filters ──────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🎛️ Filter Panel")

        all_cats = sorted(df["category"].dropna().unique().tolist())
        sel_cats = st.multiselect("Property Category", all_cats, default=[], placeholder="All categories")

        all_furn = sorted(df["furnishing"].dropna().unique().tolist())
        sel_furn = st.multiselect("Furnishing Status", all_furn, default=[], placeholder="Any furnishing")

        max_budget = int(df["sale_price"].dropna().max())
        min_budget = int(df["sale_price"].dropna().min())
        budget_range = st.slider(
            "Max Budget (₹)",
            min_value=min_budget,
            max_value=min(max_budget, 200_000_000),
            value=20_000_000,
            step=500_000,
            format="₹%d",
        )
        st.caption(f"Budget cap: **{fmt_lakh(budget_range/1e5)}**")

        all_txn = sorted(df["transaction"].dropna().unique().tolist())
        sel_txn = st.multiselect("Transaction Type", all_txn, default=[], placeholder="Any")

    # ── Main Page Filters ─────────────────────────────────────────
    mf1, mf2 = st.columns(2)
    with mf1:
        min_sqft = st.number_input("Minimum Required Area (sqft)", min_value=0, max_value=10000,
                                   value=0, step=100)
    with mf2:
        all_facing = sorted(df["facing"].dropna().unique().tolist())
        sel_facing = st.multiselect("Desired Facing Direction", all_facing, default=[],
                                    placeholder="Any direction")

    # ── Apply Filters ─────────────────────────────────────────────
    filtered = df.copy()

    if sel_cats:
        filtered = filtered[filtered["category"].isin(sel_cats)]
    if sel_furn:
        filtered = filtered[filtered["furnishing"].isin(sel_furn)]
    if sel_txn:
        filtered = filtered[filtered["transaction"].isin(sel_txn)]
    if sel_facing:
        filtered = filtered[filtered["facing"].isin(sel_facing)]

    filtered = filtered[filtered["sale_price"].fillna(0) <= budget_range]

    if min_sqft > 0:
        filtered = filtered[filtered["sqft_numeric"].fillna(0) >= min_sqft]

    # ── Results ───────────────────────────────────────────────────
    total_matches = len(filtered)
    m1, m2, m3 = st.columns(3)
    m1.metric("Matching Properties", f"{total_matches:,}")
    if total_matches > 0:
        m2.metric("Median Match Price", fmt_lakh(filtered["price_lakh"].median()))
        m3.metric("Avg Match Area", f"{filtered['sqft_numeric'].median():,.0f} sqft")

    if total_matches == 0:
        st.warning("No properties match your current filters. Try relaxing your criteria.")
    else:
        display_cols = [
            "property_name", "price", "square_feet", "facing",
            "furnishing", "status", "transaction", "description"
        ]
        show_df = filtered[display_cols].copy().reset_index(drop=True)
        show_df.columns = [
            "Property", "Listed Price", "Area", "Facing",
            "Furnishing", "Status", "Type", "Description"
        ]
        show_df["Property"] = show_df["Property"].str.strip()

        st.markdown(f"#### Showing top {min(total_matches, 200)} of {total_matches:,} matches")
        st.dataframe(
            show_df.head(200),
            use_container_width=True,
            height=520,
            column_config={
                "Property":    st.column_config.TextColumn("Property", width="large"),
                "Listed Price":st.column_config.TextColumn("Listed Price", width="small"),
                "Area":        st.column_config.TextColumn("Area", width="small"),
                "Facing":      st.column_config.TextColumn("Facing", width="small"),
                "Furnishing":  st.column_config.TextColumn("Furnishing", width="small"),
                "Status":      st.column_config.TextColumn("Status", width="medium"),
                "Type":        st.column_config.TextColumn("Type", width="small"),
                "Description": st.column_config.TextColumn("Description", width="large"),
            },
            hide_index=True,
        )

        # ── Quick distribution chart of results ──────────────────
        if total_matches > 5:
            st.markdown('<div class="section-header">Price Distribution of Results</div>', unsafe_allow_html=True)
            hist_df = filtered[filtered["price_lakh"].notna()].copy()
            fig_hist = px.histogram(
                hist_df, x="price_lakh", nbins=30,
                color_discrete_sequence=[EMERALD],
                labels={"price_lakh": "Price (₹ Lakhs)"},
            )
            fig_hist.update_layout(
                **PLOTLY_LAYOUT,
                legend=_LEGEND,
                title="Price Distribution Across Matching Properties",
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                height=280,
            )
            st.plotly_chart(fig_hist, use_container_width=True)


# ═════════════════════════════════════════════════════════════════
# PAGE 4 – SQL SHOWCASE
# ═════════════════════════════════════════════════════════════════
elif page == "💻 SQL Showcase":
    st.markdown('<div class="page-title">SQL Showcase</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Demonstrating production-grade SQL — data cleaning, window functions, and analytical queries</div>', unsafe_allow_html=True)

    QUERIES = [
        {
            "title": "1 · Duplicate Detection using ROW_NUMBER() Window Function",
            "desc": "Identifies duplicate property listings by partitioning on all meaningful columns. Only `row_num = 1` is retained in the clean table, removing 109 duplicates from the raw dataset.",
            "sql": """\
-- Detect and isolate duplicate rows using ROW_NUMBER()
-- Partitions by every meaningful column; earliest row_id is kept (row_num = 1)

CREATE TABLE surti_clean AS
WITH duplicate_cte AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY property_name,
                            areaWithType,
                            square_feet,
                            transaction,
                            status,
                            floor,
                            furnishing,
                            facing,
                            description,
                            price_per_sqft,
                            price
               ORDER BY row_id
           ) AS row_num
    FROM surti
)
SELECT *
FROM duplicate_cte
WHERE row_num = 1;   -- 109 duplicates discarded

-- Confirm: original 4524 rows → clean 4415 rows
SELECT COUNT(*) AS total_after_dedup FROM surti_clean;""",
        },
        {
            "title": "2 · Approximate Median via PERCENTILE_CONT — Price Analysis by Facing Direction",
            "desc": "MySQL lacks a native MEDIAN() function. This query approximates it using a subquery approach with AVG over the middle row, grouped by facing direction to reveal Vastu-driven price differentials.",
            "sql": """\
-- Approximate median sale_price per facing direction
-- Uses AVG of the surrounding rows at the 50th percentile position

SELECT
    facing,
    COUNT(*)                              AS total_listings,
    ROUND(AVG(sale_price) / 100000, 2)   AS avg_price_lakh,
    ROUND(
        (SELECT AVG(t2.sale_price)
         FROM (
             SELECT t1.sale_price,
                    ROW_NUMBER() OVER (
                        PARTITION BY t1.facing
                        ORDER BY t1.sale_price
                    ) AS rn,
                    COUNT(*) OVER (PARTITION BY t1.facing) AS cnt
             FROM surti_clean t1
             WHERE t1.facing = sc.facing
               AND t1.sale_price IS NOT NULL
         ) t2
         WHERE t2.rn IN (FLOOR((t2.cnt + 1) / 2),
                         CEIL((t2.cnt + 1) / 2))
        ) / 100000, 2
    )                                     AS median_price_lakh
FROM surti_clean sc
WHERE facing IS NOT NULL
  AND sale_price IS NOT NULL
GROUP BY facing
ORDER BY median_price_lakh DESC;""",
        },
        {
            "title": "3 · Price Numeric Conversion — Parsing ₹ Lac & Cr strings into Integers",
            "desc": "Raw price data arrived as formatted strings like '₹54 Lac' or '₹1.2 Cr'. This multi-step UPDATE converts both formats into a single comparable `sale_price` BIGINT column.",
            "sql": """\
-- Step 1: Add a clean numeric price column
ALTER TABLE surti_clean
ADD COLUMN sale_price BIGINT;

-- Step 2: Convert '₹X Lac' → integer (multiply by 100,000)
UPDATE surti_clean
SET sale_price =
    CAST(
        REPLACE(REPLACE(price, '₹', ''), ' Lac', '')
        AS DECIMAL(10, 2)
    ) * 100000
WHERE price LIKE '%Lac%';

-- Step 3: Convert '₹X Cr' → integer (multiply by 10,000,000)
UPDATE surti_clean
SET sale_price =
    CAST(
        REPLACE(REPLACE(price, '₹', ''), ' Cr', '')
        AS DECIMAL(12, 2)
    ) * 10000000
WHERE price LIKE '%Cr%';

-- 'Call for Price' entries remain NULL — intentional
-- Verify: 4244 non-null values, 172 NULLs (Call for Price)
SELECT
    COUNT(price)       AS raw_price_count,
    COUNT(sale_price)  AS numeric_price_count,
    COUNT(*) - COUNT(sale_price) AS null_count
FROM surti_clean;""",
        },
        {
            "title": "4 · Luxury Market Segmentation using CASE WHEN",
            "desc": "Classifies every property into a market tier for portfolio analysis. Used as the basis for the Executive Overview pie chart and scatter plot colour coding.",
            "sql": """\
-- Segment properties into market tiers by sale_price
SELECT
    CASE
        WHEN sale_price < 5000000            THEN 'Budget (<50L)'
        WHEN sale_price BETWEEN 5000000
                             AND 9999999     THEN 'Mid-Range (50L–1Cr)'
        WHEN sale_price BETWEEN 10000000
                             AND 19999999    THEN 'Premium (1Cr–2Cr)'
        WHEN sale_price >= 20000000          THEN 'Luxury (>2Cr)'
        ELSE                                      'Unknown'
    END                          AS market_segment,
    COUNT(*)                     AS total_listings,
    ROUND(COUNT(*) * 100.0
          / SUM(COUNT(*)) OVER(), 2)
                                 AS pct_share,
    ROUND(AVG(sale_price) / 100000, 2)
                                 AS avg_price_lakh,
    MIN(sale_price) / 100000     AS min_price_lakh,
    MAX(sale_price) / 100000     AS max_price_lakh
FROM surti_clean
WHERE sale_price IS NOT NULL
GROUP BY market_segment
ORDER BY MIN(sale_price);""",
        },
        {
            "title": "5 · Multi-Unit sqft Normalisation — sqft / sqyrd / sqm / acre → unified sqft_numeric",
            "desc": "Properties were listed in four different area units. This block converts all units into a single `sqft_numeric DECIMAL` column using unit-specific multipliers.",
            "sql": """\
-- Add normalised sqft column
ALTER TABLE surti_clean
ADD COLUMN sqft_numeric DECIMAL(12, 2);

-- 1) sqft — direct cast after stripping unit label
UPDATE surti_clean
SET sqft_numeric = CAST(REPLACE(square_feet, ' sqft', '') AS DECIMAL(12, 2))
WHERE square_feet LIKE '%sqft%';

-- 2) sqyrd → sqft  (1 sq yard = 9 sq ft)
UPDATE surti_clean
SET sqft_numeric = CAST(REPLACE(square_feet, ' sqyrd', '') AS DECIMAL(12, 2)) * 9
WHERE square_feet LIKE '%sqyrd%';

-- 3) acre → sqft  (1 acre = 43,560 sq ft)
UPDATE surti_clean
SET sqft_numeric = CAST(REPLACE(square_feet, ' acre', '') AS DECIMAL(12, 2)) * 43560
WHERE square_feet LIKE '%acre%';

-- 4) sqm → sqft   (1 sq metre = 10.7639 sq ft)
--    Note: comma removal required for values like '1,200 sqm'
UPDATE surti_clean
SET sqft_numeric =
    CAST(
        REPLACE(REPLACE(square_feet, ' sqm', ''), ',', '')
        AS DECIMAL(12, 2)
    ) * 10.7639
WHERE square_feet LIKE '%sqm%';

-- Validate distribution
SELECT
    MIN(sqft_numeric)  AS min_sqft,
    MAX(sqft_numeric)  AS max_sqft,
    AVG(sqft_numeric)  AS avg_sqft,
    COUNT(sqft_numeric) AS non_null_count
FROM surti_clean;""",
        },
        {
            "title": "6 · Facing Direction Standardisation — Null Invalid Values",
            "desc": "The raw `facing` column contained 176 distinct values, most being misplaced amenity names from web scraping. This query keeps only 8 valid cardinal/intercardinal directions and nulls the rest.",
            "sql": """\
-- Step 1: Standardise inconsistent spacing in direction labels
UPDATE surti_clean SET facing = TRIM(facing);

-- Step 2: Fix inconsistent dash spacing in compound directions
UPDATE surti_clean SET facing = 'North-East' WHERE facing = 'North - East';
UPDATE surti_clean SET facing = 'North-West' WHERE facing = 'North - West';
UPDATE surti_clean SET facing = 'South-East' WHERE facing = 'South - East';
UPDATE surti_clean SET facing = 'South-West' WHERE facing = 'South -West';

-- Step 3: Count values that are NOT valid directions (before nulling)
SELECT COUNT(*) AS invalid_facing_count
FROM surti_clean
WHERE facing NOT IN (
    'East', 'West', 'North', 'South',
    'North-East', 'North-West', 'South-East', 'South-West'
)
AND facing IS NOT NULL;
-- Result: 1504 misplaced values (e.g., society names, amenities)

-- Step 4: Null all invalid entries
UPDATE surti_clean
SET facing = NULL
WHERE facing NOT IN (
    'East', 'West', 'North', 'South',
    'North-East', 'North-West', 'South-East', 'South-West'
)
AND facing IS NOT NULL;

-- Final distribution of valid directions
SELECT facing, COUNT(*) AS freq
FROM surti_clean
WHERE facing IS NOT NULL
GROUP BY facing
ORDER BY freq DESC;""",
        },
    ]

    for q in QUERIES:
        with st.expander(q["title"], expanded=False):
            st.markdown(f"<div style='color:#475569; font-size:0.88rem; margin-bottom:10px;'>{q['desc']}</div>", unsafe_allow_html=True)
            st.code(q["sql"], language="sql")

    # ── Schema Reference ──────────────────────────────────────────
    st.markdown('<div class="section-header">Final Table Schema — surti_clean</div>', unsafe_allow_html=True)

    schema_data = {
        "Column": [
            "property_name", "areaWithType", "square_feet", "transaction",
            "status", "floor", "furnishing", "facing", "description",
            "price_per_sqft", "price", "row_id", "row_num",
            "sqft_numeric", "sale_price", "price_per_sqft_numeric",
        ],
        "Type": [
            "TEXT", "VARCHAR", "VARCHAR", "VARCHAR",
            "VARCHAR", "VARCHAR", "VARCHAR", "VARCHAR", "TEXT",
            "VARCHAR", "VARCHAR", "INT (PK)", "INT",
            "DECIMAL(12,2)", "BIGINT", "INT",
        ],
        "Description": [
            "Full property listing title", "Area measurement type", "Raw area string with unit",
            "New Property / Resale", "Ready to Move / Possession date",
            "Floor descriptor (e.g. '5 out of 12')", "Furnished / Semi-Furnished / Unfurnished",
            "Compass facing direction (8 valid values)", "Free-text property description",
            "Raw price-per-sqft string", "Raw listing price string",
            "Auto-increment primary key", "Row number within duplicate group (1 = kept)",
            "Normalised area in sq. ft.", "Numeric sale price in ₹", "Numeric price per sqft in ₹",
        ],
        "Nulls after Clean": [
            "~0", "6", "8", "816",
            "321", "854", "1212", "1969", "~0",
            "~0", "0", "0", "0",
            "~15", "172", "~15",
        ],
    }
    schema_df = pd.DataFrame(schema_data)
    st.dataframe(schema_df, use_container_width=True, hide_index=True,
                 column_config={
                     "Column": st.column_config.TextColumn(width="medium"),
                     "Type":   st.column_config.TextColumn(width="small"),
                     "Description": st.column_config.TextColumn(width="large"),
                     "Nulls after Clean": st.column_config.TextColumn(width="small"),
                 })

# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer-bar">'
    'Surat Real Estate Analytics Platform &nbsp;·&nbsp; '
    'Built with SQL · Python · Streamlit · Plotly'
    '</div>',
    unsafe_allow_html=True,
)
