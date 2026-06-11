# VOC Analytics Dashboard

An interactive **Voice of Customer (VOC)** analytics dashboard built with [Streamlit](https://streamlit.io/) and powered by [Snowflake](https://www.snowflake.com/). It transforms raw e-commerce product reviews into clear, decision-ready insights covering customer satisfaction, sentiment, and category-level performance.

🔗 **Live app:** (https://voc-analytics-dashboard-hbmcbsfzt95en2qe8uu9as.streamlit.app/)

---

## Features

- **KPI overview** — Total reviews, average rating, CSAT, and NPS at a glance.
- **CSAT by category** — Customer satisfaction scores broken down by product category.
- **Sentiment trends** — How customer sentiment shifts over time.
- **NPS summary** — Promoters, passives, and detractors.
- **Review explorer** — Browse and filter the underlying review data.
- **About the Data** — Built-in documentation page describing the raw data, schema, analytics views, and key analysis decisions.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend / app | Streamlit |
| Data warehouse | Snowflake |
| Charts | Altair |
| Data handling | pandas, NumPy |
| Connectivity | `snowflake-snowpark-python`, `snowflake-connector-python` |

---

## Data Model

The app reads from the `VOC_ANALYTICS.PUBLIC` schema in Snowflake.

**Tables**
- `STG_REVIEWS` — staged raw review data
- `FACT_REVIEWS` — review-level facts (rating, sentiment, category, date)
- `DIM_PRODUCT_CATEGORY` — product category dimension
- `DIM_DATE` — date dimension

**Views** (pre-aggregated for fast dashboard queries)
- `VW_KPI_SUMMARY` — headline KPIs (reviews, avg rating, CSAT)
- `VW_NPS_SUMMARY` — Net Promoter Score breakdown
- `VW_CSAT_BY_CATEGORY` — satisfaction scores by category
- `VW_SENTIMENT_TREND` — sentiment over time

---

## Running Locally

### Prerequisites
- Python 3.9+
- A Snowflake account with access to the `VOC_ANALYTICS` database

### 1. Clone and install
```bash
git clone https://github.com/navaneethak08/voc-analytics-dashboard.git
cd voc-analytics-dashboard
pip install -r requirements.txt
```

### 2. Configure Snowflake credentials
Create `.streamlit/secrets.toml` (this file is git-ignored):
```toml
[connections.snowflake]
account = "SFEDU05-GYB84614"
user = "<your_user>"
password = "<your_password>"
warehouse = "<your_warehouse>"
database = "VOC_ANALYTICS"
schema = "PUBLIC"
```

> **Note:** The `account` value uses the `ORG_NAME-ACCOUNT_NAME` format required for external connections.

### 3. Run
```bash
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`.

---

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app from the repo.
3. Set the main file path to `streamlit_app.py`.
4. Under **App settings → Secrets**, paste the same `[connections.snowflake]` block shown above.
5. Deploy. The app auto-redeploys on every push to `main`.

---

## Project Structure

```
voc-analytics-dashboard/
├── streamlit_app.py          # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml           # Dark theme configuration
└── README.md
```

---

## License

This project is for educational and demonstration purposes.
