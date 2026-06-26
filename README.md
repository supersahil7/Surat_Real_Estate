# 🏠 Surat Real Estate Analytics Platform

> **An end-to-end real estate analytics platform that transforms raw housing listings into actionable market intelligence through SQL, Python, and interactive data visualization.**

---

# 🛠️ Tech Stack & Architecture

* **Database:** MySQL *(Data Cleaning, Standardization, Deduplication, Window Functions & Advanced SQL Queries)*
* **Data Processing:** Python, Pandas *(Data Cleaning, Type Conversion, KPI Computation & Statistical Analysis)*
* **Visualization:** Streamlit, Plotly Express, Matplotlib & Seaborn *(Interactive Dashboard & Exploratory Data Analysis)*
* **Frontend:** Streamlit
* **Core Dataset:** `surti_clean_set2_2.csv`
* **Dataset Size:** **4,415 cleaned and validated property listings**

---

## 📊 Executive KPIs

* **Total Active Listings:** **4,415**

  * Represents the analyzed Surat real estate inventory.

* **Median Property Price:** **₹71.0 Lakh**

  * Reliable market midpoint, unaffected by luxury outliers.

* **Average Property Price:** **₹1.33 Crore**

  * Indicates a right-skewed market driven by premium properties.

* **Median Price per Sqft:** **₹4,698/sqft**

  * Serves as a benchmark for evaluating property value across the city.


---

# 🔍 Executive EDA Findings

## 🧭 1. Facing Direction vs Property Price

* **North (₹95L)**, **North-East (₹89.8L)** and **East (₹82L)** facing properties generally command higher median prices than South-facing properties (**₹50L**).
* Results partially support the influence of **Vastu preferences** on buyer behavior.
* **South-West** facing properties recorded the highest median price (**₹97L**), suggesting premium locality outweighs directional preference in certain micro-markets.

---

## 🏗️ 2. Area Type vs Property Valuation

* **Plot Area** properties command the highest median value at **₹6,481/sqft**, reflecting the premium associated with land ownership.
* **Super Area** and **Carpet Area** exhibit similar market valuations (~₹4,700/sqft).
* **Built Area** records the lowest median price per sqft (**₹1,786/sqft**).

---

## 🔄 3. New Property vs Resale

* **New Properties:** **₹1.065 Crore** median price.
* **Resale Properties:** **₹55 Lakh** median price.
* Newly constructed properties command nearly **2×** the valuation of resale assets.
* East-facing homes dominate new developments, whereas South-facing units appear more frequently in resale listings.

---

## 🛋️ 4. Furnishing Status Analysis

* **Unfurnished:** ₹84L
* **Furnished:** ₹65L
* **Semi-Furnished:** ₹46.25L

### Key Insight

Contrary to common expectations, **unfurnished properties recorded the highest median prices**. This occurs because premium villas, luxury apartments, and land parcels are often sold unfurnished, demonstrating a classic **Simpson's Paradox** where underlying property characteristics dominate furnishing status.

---

## 🏢 5. Floor Level Analysis

Median Prices:

* **Mid Floor (4–8):** ₹78L
* **High Floor (9+):** ₹71L
* **Low Floor (1–3):** ₹41L

### Key Insight

The market demonstrates a clear buyer preference for elevated floors, with mid-floor apartments commanding the strongest valuations.

---

## 📐 6. Property Size vs Market Value

Median Prices:

* Small (<1000 sqft): **₹34.1L**
* Medium (1000–2000 sqft): **₹66L**
* Large (2001–4000 sqft): **₹1.55 Cr**
* Luxury (>4000 sqft): **₹3.7 Cr**

### Key Insight

Property size emerged as one of the strongest predictors of market valuation, exhibiting a clear positive relationship with selling price.

---

## 💎 7. Luxury Market Segmentation

Market Distribution:

* **Budget (<₹50L):** 30.82%
* **Mid-Range (₹50L–₹1Cr):** 34.07%
* **Premium (₹1Cr–₹2Cr):** 21.07%
* **Luxury (>₹2Cr):** 18.10%

### Key Insight

Although Surat remains predominantly a **Budget–Mid Range** market, nearly one-fifth of listings belong to the luxury segment, highlighting a robust premium housing ecosystem.

---

## 🏆 8. Premium Property Analysis

The highest-valued realistic listings were primarily:

* Industrial Assets
* Commercial Showrooms
* Commercial Land
* Office Spaces

with transaction values ranging from **₹14 Cr to ₹55 Cr**.

Among residential properties, premium villas and luxury apartments located in **Piplod** and **Rundh** represented the upper end of the market.

---

## 🏠 9. Top Property Categories

Highest Median-Valued Property Types:

| Property Type  | Median Price |
| -------------- | -----------: |
| **5+ BHK**     |  **₹3.5 Cr** |
| **House**      |  **₹2.5 Cr** |
| **Showroom**   | **₹2.11 Cr** |
| **4 BHK**      |  **₹1.9 Cr** |
| **Industrial** |  **₹1.0 Cr** |

### Key Insight

Luxury residential properties dominate the high-value housing segment, while **Showrooms** emerge as the most valuable commercial asset class.

---

# 💻 Platform Features

## 📈 Executive Dashboard

* High-level KPIs
* Market Overview
* Price Distribution
* Market Segmentation
* Property Size vs Price Analysis

---

## 🧠 Buyer Insights Dashboard

Interactive analysis of:

* Facing Direction
* Floor Preferences
* Furnishing Status
* Transaction Type
* Area Type
* Property Size

---

## 🔎 Intelligent Property Finder

Allows users to filter listings based on:

* Budget
* Property Type
* Facing Direction
* Furnishing Status
* Transaction Type
* Area Type
* Property Size

and instantly returns the most relevant matching properties.

---

## 🗄️ SQL Engineering Showcase

Demonstrates advanced SQL techniques including:

* Data Cleaning & Standardization
* Duplicate Detection using `ROW_NUMBER() OVER(PARTITION BY...)`
* Common Table Expressions (CTEs)
* Window Functions
* Median Calculations
* Ranking Functions
* Business-Oriented Exploratory Data Analysis

---

# 📌 Overall Conclusion

The analysis identifies **property size, transaction type, area type, and facing direction** as the most influential factors affecting property valuation within Surat's real estate market.

While the city's inventory is primarily composed of **Budget** and **Mid-Range** housing, the presence of a substantial **Luxury Residential**, **Commercial**, and **Industrial** segment significantly elevates overall market value. The platform consolidates these findings into an interactive analytics solution, enabling buyers, investors, and analysts to explore market trends, compare property segments, and make data-driven real estate decisions.
