"""
VOC Analytics Dashboard - Enterprise Edition
Voice of Customer analytics powered by Snowflake.
"""

from datetime import date, timedelta
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.set_page_config(
    page_title="VOC Analytics | Enterprise Dashboard",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for enterprise polish
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1B2332 0%, #0E1117 100%);
        border: 1px solid rgba(41, 181, 232, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(41, 181, 232, 0.4);
        box-shadow: 0 4px 24px rgba(41, 181, 232, 0.08);
    }
    div[data-testid="stMetric"] label {
        color: #8B9DB8 !important;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #FAFAFA !important;
    }
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(41, 181, 232, 0.1);
    }
    section[data-testid="stSidebar"] .stMarkdown h1 {
        font-size: 1.1rem;
        color: #29B5E8;
        letter-spacing: 0.02em;
    }
    button[data-baseweb="tab"] {
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Constants
TIME_RANGES = ["1M", "3M", "6M", "1Y", "YTD", "All"]
CHART_HEIGHT = 320

SENTIMENT_COLORS = {
    "positive": "#00D26A",
    "neutral": "#F5A623",
    "negative": "#FF4757",
}

NPS_COLORS = {
    "Promoter": "#00D26A",
    "Passive": "#F5A623",
    "Detractor": "#FF4757",
}

CATEGORY_PALETTE = [
    "#29B5E8", "#00D26A", "#F5A623", "#FF4757",
    "#A78BFA", "#F472B6", "#38BDF8", "#34D399",
]

# Snowflake Connection
conn = st.connection("snowflake")


def _query(sql):
    df = conn.query(sql)
    df.columns = df.columns.str.lower()
    return df


# Data Loading
@st.cache_data(ttl=900, show_spinner=False)
def load_fact_reviews():
    df = _query("SELECT * FROM VOC_ANALYTICS.PUBLIC.FACT_REVIEWS")
    df["review_date"] = pd.to_datetime(df["review_date"])
    for col in ["star_rating", "sentiment_score", "is_satisfied", "review_id"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=900, show_spinner=False)
def load_csat_by_category():
    df = _query("SELECT * FROM VOC_ANALYTICS.PUBLIC.VW_CSAT_BY_CATEGORY")
    for col in ["csat_score", "avg_star_rating", "total_reviews", "satisfied_count", "positive_count", "neutral_count", "negative_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# Utility Functions
def filter_by_time_range(df, date_col, time_range):
    if time_range == "All" or df.empty:
        return df
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    max_date = df[date_col].max()
    if time_range == "1M":
        min_date = max_date - timedelta(days=30)
    elif time_range == "3M":
        min_date = max_date - timedelta(days=90)
    elif time_range == "6M":
        min_date = max_date - timedelta(days=180)
    elif time_range == "1Y":
        min_date = max_date - timedelta(days=365)
    elif time_range == "YTD":
        min_date = pd.Timestamp(date(max_date.year, 1, 1))
    else:
        return df
    return df[df[date_col] >= min_date]


def format_number(n, decimals=1):
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.{decimals}f}M"
    elif abs(n) >= 1_000:
        return f"{n/1_000:.{decimals}f}K"
    return f"{n:.{decimals}f}"


# Sidebar
with st.sidebar:
    st.markdown("# :material/analytics: VOC Analytics")
    st.caption("Voice of Customer Intelligence")
    st.divider()

    st.markdown("#### :material/filter_alt: Filters")

    reviews_df = load_fact_reviews()

    categories = ["All"] + sorted(reviews_df["product_category"].unique().tolist())
    selected_category = st.selectbox(
        "Product Category",
        categories,
        index=0,
        key="filter_category",
    )

    sentiments = ["All", "positive", "neutral", "negative"]
    selected_sentiment = st.selectbox(
        "Sentiment",
        sentiments,
        index=0,
        key="filter_sentiment",
    )

    time_range = st.segmented_control(
        "Time Range",
        TIME_RANGES,
        default="All",
        key="filter_time",
    )

    st.divider()
    st.markdown("#### :material/info: About")
    st.caption(f"**{len(reviews_df):,}** reviews analyzed")
    st.caption(f"**{reviews_df['product_category'].nunique()}** categories")
    date_range = f"{reviews_df['review_date'].min().strftime('%b %Y')} - {reviews_df['review_date'].max().strftime('%b %Y')}"
    st.caption(f"**Period:** {date_range}")

    st.divider()
    st.caption("Built with Streamlit + Snowflake")

# Apply Global Filters
filtered_df = reviews_df.copy()

if selected_category != "All":
    filtered_df = filtered_df[filtered_df["product_category"] == selected_category]

if selected_sentiment != "All":
    filtered_df = filtered_df[filtered_df["sentiment_label"] == selected_sentiment]

filtered_df = filter_by_time_range(filtered_df, "review_date", time_range)

# Page Header
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.markdown("## :material/analytics: Voice of Customer Dashboard")
    st.caption("Real-time customer sentiment intelligence across all product categories")
with header_col2:
    st.markdown("")
    if st.button(":material/restart_alt: Reset", type="tertiary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("")

# KPI Hero Row
total_reviews = len(filtered_df)
avg_rating = filtered_df["star_rating"].mean() if not filtered_df.empty else 0
csat = (filtered_df["is_satisfied"].sum() / len(filtered_df) * 100) if not filtered_df.empty else 0
promoters = len(filtered_df[filtered_df["nps_segment"] == "Promoter"])
detractors = len(filtered_df[filtered_df["nps_segment"] == "Detractor"])
nps_score = ((promoters - detractors) / total_reviews * 100) if total_reviews > 0 else 0
positive_pct = (len(filtered_df[filtered_df["sentiment_label"] == "positive"]) / total_reviews * 100) if total_reviews > 0 else 0

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric("Total Reviews", format_number(total_reviews, 0))
with kpi2:
    st.metric("Avg Rating", f"{avg_rating:.1f} / 5")
with kpi3:
    st.metric("CSAT Score", f"{csat:.1f}%")
with kpi4:
    st.metric("NPS Score", f"{nps_score:+.0f}")
with kpi5:
    st.metric("Positive Rate", f"{positive_pct:.1f}%")

st.markdown("")

# Main Content Tabs
tab_overview, tab_categories, tab_trends, tab_explorer = st.tabs([
    ":material/dashboard: Overview",
    ":material/category: Categories",
    ":material/trending_up: Trends",
    ":material/search: Review Explorer",
])

# TAB: Overview
with tab_overview:
    ov_col1, ov_col2 = st.columns([1.4, 1])

    with ov_col1:
        with st.container(border=True):
            st.markdown("**:material/donut_large: NPS Distribution**")

            nps_data = filtered_df.groupby("nps_segment").size().reset_index(name="count")
            nps_data["percentage"] = (nps_data["count"] / nps_data["count"].sum() * 100).round(1)

            base = alt.Chart(nps_data).encode(
                theta=alt.Theta("count:Q", stack=True),
                color=alt.Color(
                    "nps_segment:N",
                    scale=alt.Scale(
                        domain=list(NPS_COLORS.keys()),
                        range=list(NPS_COLORS.values()),
                    ),
                    legend=alt.Legend(title=None, orient="bottom"),
                ),
                tooltip=[
                    alt.Tooltip("nps_segment:N", title="Segment"),
                    alt.Tooltip("count:Q", title="Count", format=","),
                    alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
                ],
            )

            donut = base.mark_arc(innerRadius=60, outerRadius=120, cornerRadius=4)

            center_text = alt.Chart(pd.DataFrame({"text": [f"NPS\n{nps_score:+.0f}"]})).mark_text(
                fontSize=20, fontWeight="bold", color="#FAFAFA", lineBreak="\n"
            ).encode(text="text:N")

            st.altair_chart(
                (donut + center_text).properties(height=280),
                use_container_width=True,
            )

    with ov_col2:
        with st.container(border=True):
            st.markdown("**:material/sentiment_satisfied: Sentiment Split**")

            sent_data = filtered_df.groupby("sentiment_label").size().reset_index(name="count")
            sent_data["percentage"] = (sent_data["count"] / sent_data["count"].sum() * 100).round(1)

            sent_chart = (
                alt.Chart(sent_data)
                .mark_bar(cornerRadius=6, height=32)
                .encode(
                    x=alt.X("percentage:Q", title="Share (%)", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("sentiment_label:N", title=None, sort=["positive", "neutral", "negative"]),
                    color=alt.Color(
                        "sentiment_label:N",
                        scale=alt.Scale(
                            domain=list(SENTIMENT_COLORS.keys()),
                            range=list(SENTIMENT_COLORS.values()),
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("sentiment_label:N", title="Sentiment"),
                        alt.Tooltip("count:Q", title="Reviews", format=","),
                        alt.Tooltip("percentage:Q", title="%", format=".1f"),
                    ],
                )
                .properties(height=180)
            )

            st.altair_chart(sent_chart, use_container_width=True)

            p_col, n_col, neg_col = st.columns(3)
            pos_count = len(filtered_df[filtered_df["sentiment_label"] == "positive"])
            neu_count = len(filtered_df[filtered_df["sentiment_label"] == "neutral"])
            neg_count = len(filtered_df[filtered_df["sentiment_label"] == "negative"])
            with p_col:
                st.markdown(f"<div style='text-align:center'><span style='color:#00D26A;font-size:1.4rem;font-weight:700'>{pos_count:,}</span><br><span style='color:#8B9DB8;font-size:0.75rem'>Positive</span></div>", unsafe_allow_html=True)
            with n_col:
                st.markdown(f"<div style='text-align:center'><span style='color:#F5A623;font-size:1.4rem;font-weight:700'>{neu_count:,}</span><br><span style='color:#8B9DB8;font-size:0.75rem'>Neutral</span></div>", unsafe_allow_html=True)
            with neg_col:
                st.markdown(f"<div style='text-align:center'><span style='color:#FF4757;font-size:1.4rem;font-weight:700'>{neg_count:,}</span><br><span style='color:#8B9DB8;font-size:0.75rem'>Negative</span></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**:material/star: Rating Distribution**")

        rating_data = filtered_df.groupby("star_rating").size().reset_index(name="count")
        rating_data["star_rating"] = rating_data["star_rating"].astype(str) + " star"

        rating_chart = (
            alt.Chart(rating_data)
            .mark_bar(cornerRadius=6, color="#29B5E8")
            .encode(
                x=alt.X("star_rating:O", title=None, sort=["1 star", "2 star", "3 star", "4 star", "5 star"]),
                y=alt.Y("count:Q", title="Reviews"),
                tooltip=[
                    alt.Tooltip("star_rating:O", title="Rating"),
                    alt.Tooltip("count:Q", title="Count", format=","),
                ],
            )
            .properties(height=220)
        )
        st.altair_chart(rating_chart, use_container_width=True)


# TAB: Categories
with tab_categories:
    cat_data = load_csat_by_category()

    cat_col1, cat_col2 = st.columns([1.2, 1])

    with cat_col1:
        with st.container(border=True):
            st.markdown("**:material/leaderboard: CSAT Score by Category**")

            csat_chart = (
                alt.Chart(cat_data)
                .mark_bar(cornerRadius=6)
                .encode(
                    x=alt.X("csat_score:Q", title="CSAT %", scale=alt.Scale(domain=[0, 50])),
                    y=alt.Y("product_category:N", title=None, sort="-x"),
                    color=alt.Color(
                        "csat_score:Q",
                        scale=alt.Scale(scheme="viridis"),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("product_category:N", title="Category"),
                        alt.Tooltip("csat_score:Q", title="CSAT %", format=".1f"),
                        alt.Tooltip("total_reviews:Q", title="Reviews", format=","),
                        alt.Tooltip("avg_star_rating:Q", title="Avg Rating", format=".2f"),
                    ],
                )
                .properties(height=CHART_HEIGHT)
            )
            st.altair_chart(csat_chart, use_container_width=True)

    with cat_col2:
        with st.container(border=True):
            st.markdown("**:material/pie_chart: Review Volume by Category**")

            vol_chart = (
                alt.Chart(cat_data)
                .mark_arc(innerRadius=50, outerRadius=110, cornerRadius=3)
                .encode(
                    theta=alt.Theta("total_reviews:Q", stack=True),
                    color=alt.Color(
                        "product_category:N",
                        scale=alt.Scale(range=CATEGORY_PALETTE),
                        legend=alt.Legend(title=None, orient="bottom", columns=2),
                    ),
                    tooltip=[
                        alt.Tooltip("product_category:N", title="Category"),
                        alt.Tooltip("total_reviews:Q", title="Reviews", format=","),
                    ],
                )
                .properties(height=280)
            )
            st.altair_chart(vol_chart, use_container_width=True)

    with st.container(border=True):
        st.markdown("**:material/grid_view: Sentiment Heatmap by Category**")

        heat_data = filtered_df.groupby(["product_category", "sentiment_label"]).size().reset_index(name="count")
        total_per_cat = heat_data.groupby("product_category")["count"].transform("sum")
        heat_data["pct"] = (heat_data["count"] / total_per_cat * 100).round(1)

        heatmap = (
            alt.Chart(heat_data)
            .mark_rect(cornerRadius=4)
            .encode(
                x=alt.X("sentiment_label:N", title=None, sort=["positive", "neutral", "negative"]),
                y=alt.Y("product_category:N", title=None, sort=alt.EncodingSortField(field="pct", op="max", order="descending")),
                color=alt.Color("pct:Q", scale=alt.Scale(scheme="inferno"), legend=alt.Legend(title="% Share")),
                tooltip=[
                    alt.Tooltip("product_category:N", title="Category"),
                    alt.Tooltip("sentiment_label:N", title="Sentiment"),
                    alt.Tooltip("count:Q", title="Reviews", format=","),
                    alt.Tooltip("pct:Q", title="Share %", format=".1f"),
                ],
            )
            .properties(height=280)
        )

        text = (
            alt.Chart(heat_data)
            .mark_text(fontSize=12, fontWeight="bold", color="#FAFAFA")
            .encode(
                x=alt.X("sentiment_label:N", sort=["positive", "neutral", "negative"]),
                y=alt.Y("product_category:N", sort=alt.EncodingSortField(field="pct", op="max", order="descending")),
                text=alt.Text("pct:Q", format=".1f"),
            )
        )

        st.altair_chart(heatmap + text, use_container_width=True)


# TAB: Trends
with tab_trends:
    with st.container(border=True):
        st.markdown("**:material/show_chart: Sentiment Volume Over Time**")

        daily_trend = (
            filtered_df
            .groupby([filtered_df["review_date"].dt.to_period("W").dt.start_time, "sentiment_label"])
            .size()
            .reset_index(name="count")
        )
        daily_trend.columns = ["week", "sentiment_label", "count"]

        trend_chart = (
            alt.Chart(daily_trend)
            .mark_area(opacity=0.6, line=True)
            .encode(
                x=alt.X("week:T", title=None),
                y=alt.Y("count:Q", title="Weekly Reviews", stack=True),
                color=alt.Color(
                    "sentiment_label:N",
                    scale=alt.Scale(
                        domain=list(SENTIMENT_COLORS.keys()),
                        range=list(SENTIMENT_COLORS.values()),
                    ),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("week:T", title="Week", format="%b %d, %Y"),
                    alt.Tooltip("sentiment_label:N", title="Sentiment"),
                    alt.Tooltip("count:Q", title="Reviews", format=","),
                ],
            )
            .properties(height=CHART_HEIGHT)
        )
        st.altair_chart(trend_chart, use_container_width=True)

    tr_col1, tr_col2 = st.columns(2)

    with tr_col1:
        with st.container(border=True):
            st.markdown("**:material/trending_up: Weekly Avg Rating Trend**")

            weekly_rating = (
                filtered_df
                .groupby(filtered_df["review_date"].dt.to_period("W").dt.start_time)
                .agg(avg_rating=("star_rating", "mean"), review_count=("review_id", "count"))
                .reset_index()
            )
            weekly_rating.columns = ["week", "avg_rating", "review_count"]
            weekly_rating["avg_rating"] = weekly_rating["avg_rating"].round(2)
            weekly_rating["ma_4w"] = weekly_rating["avg_rating"].rolling(4, min_periods=1).mean().round(2)

            rating_line = alt.Chart(weekly_rating).encode(
                x=alt.X("week:T", title=None),
                tooltip=[
                    alt.Tooltip("week:T", title="Week", format="%b %d, %Y"),
                    alt.Tooltip("avg_rating:Q", title="Avg Rating", format=".2f"),
                    alt.Tooltip("ma_4w:Q", title="4-Week MA", format=".2f"),
                    alt.Tooltip("review_count:Q", title="Reviews", format=","),
                ],
            )

            points = rating_line.mark_circle(size=30, opacity=0.5, color="#29B5E8").encode(
                y=alt.Y("avg_rating:Q", title="Rating", scale=alt.Scale(domain=[1, 5])),
            )

            ma_line = rating_line.mark_line(strokeWidth=3, color="#00D26A").encode(
                y=alt.Y("ma_4w:Q", scale=alt.Scale(domain=[1, 5])),
            )

            st.altair_chart((points + ma_line).properties(height=260), use_container_width=True)

    with tr_col2:
        with st.container(border=True):
            st.markdown("**:material/speed: Weekly NPS Trend**")

            weekly_nps = filtered_df.copy()
            weekly_nps["week"] = weekly_nps["review_date"].dt.to_period("W").dt.start_time

            nps_weekly = weekly_nps.groupby("week").apply(
                lambda g: pd.Series({
                    "nps": ((g["nps_segment"] == "Promoter").sum() - (g["nps_segment"] == "Detractor").sum()) / len(g) * 100,
                    "count": len(g),
                })
            ).reset_index()
            nps_weekly["nps"] = nps_weekly["nps"].round(1)
            nps_weekly["ma_4w"] = nps_weekly["nps"].rolling(4, min_periods=1).mean().round(1)

            nps_base = alt.Chart(nps_weekly).encode(
                x=alt.X("week:T", title=None),
                tooltip=[
                    alt.Tooltip("week:T", title="Week", format="%b %d, %Y"),
                    alt.Tooltip("nps:Q", title="NPS", format="+.1f"),
                    alt.Tooltip("ma_4w:Q", title="4-Week MA", format="+.1f"),
                ],
            )

            nps_bars = nps_base.mark_bar(opacity=0.4, color="#29B5E8").encode(
                y=alt.Y("nps:Q", title="NPS Score"),
            )

            nps_ma = nps_base.mark_line(strokeWidth=3, color="#F5A623").encode(
                y=alt.Y("ma_4w:Q"),
            )

            zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
                strokeDash=[4, 4], color="#8B9DB8", opacity=0.5
            ).encode(y="y:Q")

            st.altair_chart((nps_bars + nps_ma + zero_rule).properties(height=260), use_container_width=True)

    with st.container(border=True):
        st.markdown("**:material/stacked_line_chart: Monthly CSAT by Category**")

        monthly_csat = (
            filtered_df
            .groupby([filtered_df["review_date"].dt.to_period("M").dt.start_time, "product_category"])
            .agg(csat=("is_satisfied", "mean"))
            .reset_index()
        )
        monthly_csat.columns = ["month", "product_category", "csat"]
        monthly_csat["csat"] = (monthly_csat["csat"] * 100).round(1)

        csat_line = (
            alt.Chart(monthly_csat)
            .mark_line(strokeWidth=2.5)
            .encode(
                x=alt.X("month:T", title=None),
                y=alt.Y("csat:Q", title="CSAT %", scale=alt.Scale(zero=False)),
                color=alt.Color(
                    "product_category:N",
                    scale=alt.Scale(range=CATEGORY_PALETTE),
                    legend=alt.Legend(title=None, orient="bottom", columns=4),
                ),
                tooltip=[
                    alt.Tooltip("month:T", title="Month", format="%b %Y"),
                    alt.Tooltip("product_category:N", title="Category"),
                    alt.Tooltip("csat:Q", title="CSAT %", format=".1f"),
                ],
            )
            .properties(height=CHART_HEIGHT)
        )
        st.altair_chart(csat_line, use_container_width=True)


# TAB: Review Explorer
with tab_explorer:
    exp_col1, exp_col2 = st.columns([2, 1])

    with exp_col1:
        search_term = st.text_input(
            ":material/search: Search reviews",
            placeholder="Type keywords to filter reviews...",
            key="search_reviews",
        )

    with exp_col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Most Recent", "Highest Rated", "Lowest Rated"],
            key="sort_reviews",
        )

    explorer_df = filtered_df.copy()

    if search_term:
        explorer_df = explorer_df[
            explorer_df["review_text"].str.contains(search_term, case=False, na=False)
        ]

    if sort_by == "Most Recent":
        explorer_df = explorer_df.sort_values("review_date", ascending=False)
    elif sort_by == "Highest Rated":
        explorer_df = explorer_df.sort_values("star_rating", ascending=False)
    else:
        explorer_df = explorer_df.sort_values("star_rating", ascending=True)

    st.caption(f"Showing **{min(100, len(explorer_df)):,}** of **{len(explorer_df):,}** reviews")

    display_df = explorer_df.head(100)[
        ["review_date", "product_category", "star_rating", "sentiment_label", "nps_segment", "review_text"]
    ].copy()
    display_df.columns = ["Date", "Category", "Rating", "Sentiment", "NPS Segment", "Review"]
    display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")

    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        hide_index=True,
        column_config={
            "Rating": st.column_config.NumberColumn("Rating", format="%d / 5"),
            "Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
            "NPS Segment": st.column_config.TextColumn("NPS", width="small"),
            "Review": st.column_config.TextColumn("Review", width="large"),
        },
    )
