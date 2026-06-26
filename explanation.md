# Surat Real Estate Analytics — Complete Interview Guide

---

## HOW TO USE THIS DOCUMENT

This guide walks through every KPI, every chart, every EDA finding, and every critical piece of visualization code in your dashboard — written so you can explain each decision confidently in an interview. Each section ends with a "Say it in an interview" block: a natural, confident answer you can practise out loud.

---

# PART 1 — DATA PIPELINE & ENGINEERING DECISIONS

## 1.1 Why `on_bad_lines='skip'`?

```python
df = pd.read_csv("surti_clean_set2.csv", on_bad_lines="skip")
```

**The problem:** Line 2847 in the CSV contains an unescaped double quote inside a property description. The default CSV parser treats it as the start of a new field, breaks the row structure, and raises a `ParserError` — crashing the entire app before a single chart renders.

**The fix:** `on_bad_lines='skip'` tells pandas to silently discard any row that cannot be parsed correctly. Since it affects only 1–2 rows out of 4,415, the analytical impact is negligible.

**Why not `error_bad_lines=False`?** That's the deprecated pandas <1.3 parameter. `on_bad_lines='skip'` is the modern equivalent and future-proof.

> **Say it:** "The raw CSV had a malformed row caused by an unescaped quote in a description field. Rather than crashing the app, I used `on_bad_lines='skip'` to silently drop that one row — a negligible loss of one record out of 4,415 — and keep the pipeline running cleanly."

---

## 1.2 `pd.to_numeric(errors='coerce')`

```python
for col in ["sale_price", "sqft_numeric", "price_per_sqft_numeric"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
```

**Why:** Although these columns were already converted to numbers in SQL, the CSV export can occasionally store them as strings — especially if the column had mixed NULL representations. `errors='coerce'` converts anything that can't be parsed to `NaN` rather than raising an exception. This makes all downstream `.median()`, `.mean()`, and comparison operations safe.

> **Say it:** "I defensively re-cast the three numeric columns on load. If any value couldn't be parsed — say a stray 'NULL' string left over from the SQL export — `errors='coerce'` silently converts it to NaN instead of crashing. It's a one-line safety net that makes the entire dashboard resilient."

---

## 1.3 Feature Engineering in `load_data()`

### Property Category (`category` column)

```python
m = re.search(
    r"^(\d+\s*BHK|House|Land|Office Space|Shop|Showroom|...)",
    name, re.IGNORECASE,
)
return m.group(1).strip() if m else "Other"
```

**The problem:** The raw `property_name` column contains strings like `"3 BHK Flat for Sale in Adajan Surat"`. There is no pre-existing category column. A recruiter would call this **feature extraction from unstructured text**.

**The technique:** A regex anchored at `^` (start of string) matches the first meaningful token — the property type. `re.IGNORECASE` handles casing inconsistencies. `.strip()` removes leading/trailing whitespace artifacts from scraping.

**Why not `.split()[0]`?** Because "Office Space" is two words. A simple split would give "Office", not "Office Space". The regex handles multi-word categories correctly.

---

### Floor Bucketing (`floor_bucket` column)

```python
num = int(str(f).split(" out of ")[0])
if num <= 3:   return "Low (1–3)"
elif num <= 8: return "Mid (4–8)"
else:          return "High (9+)"
```

**The problem:** Floor data is stored as `"5 out of 12"` — a human-readable string, not a number. You cannot do arithmetic on it directly.

**The technique:** Split on the string `" out of "`, take the first part (the actual floor number), cast to int, then bin into three buckets. The `try/except` wrapper handles any remaining dirty values.

**Why these bucket sizes?** Ground floor is a property in itself (separate entrance, garden access). Low (1–3) is walk-up territory — no elevator dependency. Mid (4–8) is the sweet spot — elevator access, some height, but not exposed. High (9+) is premium but limited buyer pool due to water pressure, evacuation concerns, and elevator dependency.

---

### Market Segmentation (`segment` column)

```python
if p < 5_000_000:   return "Budget (<50L)"
elif p < 10_000_000: return "Mid-Range (50L–1Cr)"
elif p < 20_000_000: return "Premium (1Cr–2Cr)"
else:               return "Luxury (>2Cr)"
```

**Why these thresholds?** These aren't arbitrary. ₹50L is the approximate upper limit of affordable housing in a Tier-2 Indian city. ₹1 Cr is the psychological "crore barrier" that separates aspirational from premium. ₹2 Cr+ is where ultra-luxury and commercial properties sit.

---

### `@st.cache_data`

```python
@st.cache_data
def load_data():
    ...
```

**Why:** Every widget interaction in Streamlit re-runs the entire script from top to bottom. Without caching, the CSV would be read, parsed, and all feature engineering would repeat on every slider move or button click. `@st.cache_data` runs `load_data()` only once, stores the result in memory, and returns it instantly on all subsequent calls. This is what makes the dashboard feel instant.

> **Say it:** "Streamlit re-executes the script on every user interaction. I decorated the data loading function with `@st.cache_data` so the CSV parsing and feature engineering — which includes regex extraction and floor bucketing across 4,415 rows — only runs once. Every subsequent interaction returns the cached DataFrame instantly."

---

## 1.4 The `PLOTLY_LAYOUT` Pattern

```python
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#334155"),
    margin=dict(l=10, r=10, t=40, b=10),
    title_font=dict(size=14, color="#1a3a4a"),
)
```

**Why:** This is the DRY (Don't Repeat Yourself) principle applied to chart styling. Every chart in the dashboard uses `**PLOTLY_LAYOUT` to unpack these settings. If you want to change the font across all 8 charts, you change one line. Both `paper_bgcolor` and `plot_bgcolor` are set to transparent `rgba(0,0,0,0)` so charts blend into the custom CSS background rather than showing Plotly's default white box.

**The `legend` fix:** The original version stored `legend=` inside `PLOTLY_LAYOUT`, which caused a `TypeError: multiple values for keyword argument 'legend'` whenever a chart also passed its own `legend=`. The fix was to remove it from the dict and add `legend=_LEGEND` per chart, avoiding the Python keyword collision.

---

# PART 2 — KPIs (Executive Overview)

KPIs are the first thing a stakeholder reads. Each one was chosen to answer a specific business question in one glance.

---

## KPI 1: Total Properties — `4,415`

```python
total = len(df)
```

**What it answers:** How large is this market sample? Is the dataset big enough to trust?

**Why `len(df)` and not `df['sale_price'].count()`?** Because we want the total number of listings, not just the ones with a price. A property listed as "Call for Price" still exists in the market.

---

## KPI 2: Median Price — `₹71L`

```python
med_lakh = df["price_lakh"].median()
```

**Why median, not mean?** Real estate price distributions are severely right-skewed. A single ₹55 Crore industrial shed in the dataset would pull the mean upward by crores, making it useless as a "typical price" signal. The median is the price at which exactly half the market is cheaper and half is more expensive — it's the true middle-market number.

**Why show it in Lakhs?** Because ₹71 Lakhs is more readable and relatable than ₹71,00,000 or ₹0.71 Crores for a mid-market buyer.

> **Say it:** "I deliberately chose median over mean because real estate data is heavily skewed by luxury outliers — a ₹55 Crore commercial shed would drag the mean upward by crores and mislead the reader. Median gives you the true market midpoint."

---

## KPI 3: Average Price — `₹1.33 Cr`

```python
avg_cr = df["sale_price"].mean() / 1e7
```

**Why show average if median is better?** Average and median tell different stories. When average (₹1.33 Cr) is significantly higher than median (₹71L), it signals a long right tail — the luxury segment is pulling the average up. Showing both lets an analyst immediately understand the skew without looking at a single chart.

**Why show in Crores here?** Because at ₹1.33 Cr the Crore unit is natural — it would be `₹133 Lakhs` otherwise, which is harder to process.

---

## KPI 4: Average Price/Sqft

```python
avg_psf = df["price_per_sqft_numeric"].mean()
```

**Why:** Price per sqft is the universal unit of comparison in real estate — it normalises for property size. A 500 sqft flat at ₹50L and a 1000 sqft flat at ₹1 Cr are "the same price per sqft" even though the absolute prices differ by 2x. This KPI lets investors compare locations fairly.

---

## KPI 5: Median Price/Sqft

```python
med_psf = df["price_per_sqft_numeric"].median()
```

**Why both average and median for Price/Sqft?** Same skew reasoning as for total price. Plot Area (land) has extremely high per-sqft values while Built Area has very low values. The median gives the typical rate a buyer or developer should expect, while the average signals the luxury end's pull.

---

## KPI Card Code Pattern

```python
def kpi(label, value, sub=""):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""

c1.markdown(kpi("Median Price", fmt_lakh(med_lakh), "50th percentile"), unsafe_allow_html=True)
```

**Why custom HTML instead of `st.metric()`?** `st.metric()` is functional but has a fixed, rigid style. Custom HTML cards allow the dark gradient background, serif display font (Playfair Display), monospaced metric values, and the subtle subtitle — things that make the dashboard look production-grade rather than a student project. `unsafe_allow_html=True` is required because Streamlit's Markdown renderer by default strips HTML tags for security.

---

# PART 3 — CHARTS & VISUALIZATION TECHNIQUES

## Chart 1: Donut Pie Chart — Market Segmentation

**Page:** Executive Overview
**Library call:** `px.pie(..., hole=0.52)`

### What it shows
The proportion of listings in each of four price tiers: Budget (<50L), Mid-Range (50L–1Cr), Premium (1Cr–2Cr), Luxury (>2Cr).

### Why a Donut Chart (not a regular pie)?
A solid pie chart forces the reader to estimate angles, which humans do poorly. A donut chart:
1. Creates a visual centre that you can use for annotation (we placed the total listing count there).
2. Makes the arc lengths slightly easier to compare than wedge areas.
3. Looks more modern and less cluttered.

`hole=0.52` means 52% of the chart's radius is hollow — a common professional ratio.

### Key code decisions

```python
seg_df["Segment"] = pd.Categorical(seg_df["Segment"], categories=seg_order, ordered=True)
seg_df = seg_df.sort_values("Segment")
```
Without this, Plotly would render segments in random order. By making it an ordered `pd.Categorical`, the segments always appear Budget → Mid → Premium → Luxury clockwise.

```python
custom_data=["Share"],
hovertemplate="<b>%{label}</b><br>%{value:,} properties (%{customdata[0]:.1f}%)<extra></extra>"
```
`custom_data` passes extra columns into the hover. `%{customdata[0]:.1f}%` formats the percentage to one decimal. `<extra></extra>` removes Plotly's default trace name box from the tooltip, making it cleaner.

```python
annotations=[dict(text=f"<b>{total:,}</b><br>listings", x=0.5, y=0.5, ...)]
```
This places text exactly at the centre of the donut hole. `x=0.5, y=0.5` in Plotly's coordinate system means the paper centre. The annotation is not a data point — it's a static label rendered on the figure's paper layer.

### EDA Finding
Budget + Mid-Range = ~65% of listings. Luxury (>2Cr) = 18%. This means Surat is a mid-market city with a surprisingly active luxury segment.

> **Say it:** "I chose a donut chart over a bar chart for segmentation because the core question is 'what share of the market is each tier?' — that's a part-of-whole question, and pie/donut charts are the right tool for it. I added an annotation in the centre with the total listing count so the reader immediately knows the sample size."

---

## Chart 2: Scatter Plot — Property Size vs Price

**Page:** Executive Overview
**Library call:** `px.scatter(..., color="Segment", opacity=0.55)`

### What it shows
The relationship between a property's area (sqft) and its price (₹ Crores), coloured by market segment.

### Why a Scatter Plot?
Scatter plots are the correct tool for exploring the relationship between two continuous variables. Here the hypothesis is: "larger properties cost more." The scatter plot both confirms this and reveals exceptions — small premium-segment properties that are expensive due to location, not size.

### Key code decisions

```python
scatter_df = df[
    df["sqft_numeric"].notna() &
    df["sale_price"].notna() &
    (df["sqft_numeric"] <= 10_000)
].copy()
```
The `<= 10,000 sqft` filter removes a handful of massive industrial sheds and agricultural land plots (up to 291,000 sqft). Without this filter, the x-axis would span 0 to 291,000 sqft and all residential properties would be compressed into a tiny band on the left — making the chart unreadable. This is called **outlier trimming for visual clarity**, and you should always justify it (the outliers are not deleted from the data, only hidden in this chart).

```python
opacity=0.55
```
With 4,000+ data points, overlapping dots (overplotting) makes the chart look like a blob. Partial transparency (`opacity=0.55`) lets overlapping points appear darker than isolated points, revealing density naturally.

```python
color="Segment", color_discrete_map=SEG_COLORS
```
The same four colours used in the pie chart are reused here. This is called **consistent colour encoding** — a core data visualisation principle. Once a reader learns that red = Luxury from the pie chart, seeing red dots in the scatter plot immediately communicates "expensive" without re-reading the legend.

### EDA Finding
Strong positive correlation between size and price. But there are red (Luxury) dots even in the 500–1000 sqft range — this reveals location-driven pricing in premium Surat localities like Piplod.

---

## Chart 3: Horizontal Bar Chart — Median Price by Property Category

**Page:** Executive Overview
**Library call:** `px.bar(..., orientation="h", color="Median Price (L)", color_continuous_scale=[...])`

### What it shows
The median price for each property type (2 BHK, 3 BHK, Shop, Showroom, etc.), sorted high to low.

### Why Horizontal (not Vertical)?
Category names like "Office Space" and "Industrial" are long strings. On a vertical bar chart they would need to be rotated 45° or truncated — both reduce readability. Horizontal bars give each label its own full row, making scanning effortless.

### Why colour-encode the bars if they're already sorted by value?
This is a deliberate choice called **redundant encoding** — using both position AND colour to encode the same variable. It helps readers who are colourblind (position still works) and makes the gradient visually meaningful even for those who jump to a random bar in the middle of the chart.

```python
color_continuous_scale=["#bfdbfe", "#3b82f6", "#1d4ed8"]
```
A three-stop blue gradient: light blue (low price) → medium blue → dark blue (high price). This avoids the misleading association of red = bad / green = good that some colour schemes imply.

```python
yaxis=dict(autorange="reversed")
```
By default, Plotly renders horizontal bars with the first category at the bottom. `autorange="reversed"` flips this so the highest-priced category appears at the top — which matches how readers expect ranked lists to work (best at top).

```python
.head(12)
```
Only the top 12 categories are shown. Displaying all 16+ categories (including rare types like "10 BHK" with 2 properties) would dilute the chart with statistically unreliable values.

### EDA Finding
5+ BHK and 6 BHK residential properties and commercial types (Showroom, Office Space) dominate the upper market. 1 BHK and Plot categories occupy the bottom.

---

## Chart 4: Bar Chart — Facing Direction vs Median Price (Vastu Analysis)

**Page:** Buyer Insights
**Library call:** `px.bar(..., color="Vastu")`

### What it shows
The median sale price grouped by which compass direction a property faces, with Vastu-preferred directions (North, North-East, East) highlighted in emerald green.

### Why is this EDA significant?
Vastu Shastra is an ancient Indian architectural science that influences real estate purchase decisions — particularly in Gujarat. North and North-East facing properties are believed to attract wealth and positive energy. If buyers pay a premium for these directions, it would appear as higher median prices — and it does.

### Key code decisions

```python
VASTU_GOOD = {"North", "North-East", "East"}
facing_df["Vastu"] = facing_df["facing"].apply(
    lambda x: "Vastu-Preferred" if x in VASTU_GOOD else "Other"
)
```
Using a Python `set` for membership testing is O(1) — more efficient than a list comparison. This creates a binary colour variable that drives the green/grey colouring of bars.

```python
color_discrete_map={"Vastu-Preferred": EMERALD, "Other": "#64748b"}
```
Emerald green (#10b981) for Vastu-preferred directions visually communicates "positive signal." Slate grey (#64748b) for others is intentionally neutral — neither positive nor negative — so it doesn't compete for attention.

### EDA Finding
North (₹95L), North-East (₹89.8L), East (₹82L) all command strong medians. But South-West (₹97L) is the anomaly — it commands the highest median price despite not being Vastu-preferred. This is likely a **confounding location effect**: South-West facing properties in Surat happen to be clustered in premium micro-markets like Vesu or Pal, so location drives the price more than direction.

> **Say it:** "What's interesting is South-West has the highest median despite not being Vastu-preferred. This is a classic confounding variable situation — South-West facing properties in our dataset happen to cluster in premium Surat localities. So direction is correlated with price, but location is the actual driver. That's an important nuance I highlight in the insight box."

---

## Chart 5: Bar Chart — Area Type vs Median Price/Sqft

**Page:** Buyer Insights

### What it shows
Median price per square foot grouped by the area measurement type: Carpet Area, Super Area, Built Area, Plot Area.

### Why is this EDA important?
These aren't just labelling conventions — they represent fundamentally different things:
- **Plot Area:** You're buying raw land. No construction cost included. Price per sqft reflects pure land value.
- **Carpet Area:** Usable floor space inside walls. The most honest measure.
- **Super Area:** Includes walls, elevator shaft, common corridors — always larger than carpet area. Builders prefer quoting price per super sqft to make it look cheaper.
- **Built Area:** Intermediate — typically includes walls but not common areas.

### EDA Finding
Plot Area: ₹6,481/sqft → highest (pure land premium in a densely developed city).
Super Area: ₹4,700/sqft → inflated denominator makes it look cheaper.
Carpet Area: ₹4,657/sqft → true usable area, slightly cheaper per unit.
Built Area: ₹1,786/sqft → lowest, likely older or peripheral properties.

```python
color_continuous_scale=["#fef3c7", "#f59e0b", "#b45309"]
```
An amber gradient — chosen to visually distinguish this chart's variable (land value) from the blue used in the category chart. Colour palette variation across charts prevents visual fatigue and helps readers track which chart they're looking at.

---

## Chart 6: Notched Box Plot — New Property vs Resale

**Page:** Buyer Insights
**Library call:** `px.box(..., notched=True, points="outliers")`

### What it shows
The full price distribution — minimum, Q1, median, Q3, maximum, and outliers — for New Properties vs Resale properties.

### Why a Box Plot (not a bar chart of medians)?
A bar chart of medians shows you one number per group. A box plot shows you the entire distribution:
- **The box:** Middle 50% of values (IQR — Interquartile Range)
- **The line inside:** Median
- **The whiskers:** Typical range (1.5× IQR from box edges)
- **The dots:** Outliers beyond the whiskers

This is crucial here because resale properties have an extremely wide spread — some are cheap inherited flats, others are premium secondary market villas.

### Why `notched=True`?
Notches represent the 95% confidence interval around the median. When the notches of two boxes do NOT overlap, the medians are statistically significantly different. This turns a visual comparison into a quasi-statistical test — something you can defend analytically, not just visually.

### Key code decisions

```python
cap = txn_df.groupby("transaction")["Price (₹ Cr)"].quantile(0.95)
txn_df = txn_df[
    txn_df.apply(lambda r: r["Price (₹ Cr)"] <= cap[r["transaction"]], axis=1)
]
```
The box plot is capped at the 95th percentile **per group**. Without this, the ₹53 Cr industrial shed would extend the y-axis so far that the residential boxes would be squashed to 1% of chart height. The cap is applied separately per group to avoid one group's outlier affecting the other's scale.

### EDA Finding
New Property median: ~₹1.065 Cr. Resale median: ~₹55L. New properties are nearly double the price. The non-overlapping notches confirm this isn't a sampling artifact. This finding tells buyers: if you want a bargain, the resale market is where to look.

> **Say it:** "I used a notched box plot specifically because I wanted to go beyond just showing medians. The notches give you a visual confidence interval — when the notches of New Property and Resale don't overlap, you can say with statistical confidence that the medians are genuinely different, not just a random sample variation."

---

## Chart 7: Bar Chart — Floor Level vs Median Price

**Page:** Buyer Insights

### What it shows
Median price across four floor buckets: Ground, Low (1–3), Mid (4–8), High (9+).

### The Floor Bucketing Logic

```python
num = int(str(f).split(" out of ")[0])
```
The raw value is `"5 out of 12"`. Splitting on `" out of "` and taking index `[0]` gives `"5"`. Casting to `int` allows numeric comparison for bucketing. The `try/except` handles edge cases like `"Ground"` (caught before this line) or any remaining dirty string.

```python
floor_order = ["Ground", "Low (1–3)", "Mid (4–8)", "High (9+)"]
floor_df["floor_bucket"] = pd.Categorical(floor_df["floor_bucket"], categories=floor_order, ordered=True)
floor_df = floor_df.sort_values("floor_bucket")
```
Without `pd.Categorical`, `.sort_values()` would sort alphabetically: Ground → High → Low → Mid. That's meaningless. Making it an ordered Categorical forces the physically correct order: Ground < Low < Mid < High.

### EDA Finding
Mid (4–8): ₹78L → highest. High (9+): ₹71L → slightly less. Low (1–3): lower. Ground: lowest.

The counterintuitive result (Mid > High) is explained by buyer psychology: mid-floor units have elevator access but avoid the very high floors that carry concerns about water pressure, fire safety, and elevator dependency. Premium builders also place signature amenities on mid floors (swimming pools, gyms) making them the desirable tier.

---

## Chart 8: Bar Chart — Furnishing vs Median Price

**Page:** Buyer Insights

### EDA Finding — The Counterintuitive Result
Unfurnished: ₹84L → highest. Furnished: ₹65L. Semi-Furnished: ₹46.25L.

You'd expect furnished properties to cost more (furniture has value). Why is unfurnished highest?

**The answer is a confounding variable.** Expensive properties — large plots, luxury villas, commercial spaces — are almost always sold unfurnished. You don't buy a ₹3 Crore plot with furniture. The furnishing status is correlated with property type, and property type drives price. This is called **Simpson's Paradox** in statistics — a trend that appears in data but reverses when you control for a lurking variable.

> **Say it:** "The furnishing result looks counterintuitive — unfurnished properties have the highest median. But this is actually a classic case of a confounding variable. Large plots, industrial sheds, and luxury villas are all sold unfurnished and they're extremely expensive. If I controlled for property type, I expect the unfurnished premium would disappear or reverse within each type. I mentioned this in the insight box precisely because it's the kind of finding that separates a careful analyst from one who reads numbers at face value."

---

## Chart 9: Histogram — Property Finder Price Distribution

**Page:** Property Finder (dynamic, updates per filter)
**Library call:** `px.histogram(..., nbins=30)`

### What it shows
The price distribution of only the properties matching the current filter selection. This updates in real time as the user adjusts filters.

### Why 30 bins?
`nbins=30` is a good default for distributions in the 50–500 record range. Too few bins (e.g., 5) loses shape information; too many (e.g., 200) creates a spiky, noisy chart. Plotly may adjust the actual bin count slightly based on the data range — `nbins` is a target, not an exact value.

### Why is this chart only shown when `total_matches > 5`?

```python
if total_matches > 5:
```
A histogram with 3 properties is meaningless. The `> 5` guard prevents rendering a nonsensical chart. This is a defensive UI pattern: only show a visualisation when there's enough data to make it meaningful.

---

# PART 4 — ALL EDA FINDINGS (WITH DEEPER EXPLANATIONS)

## EDA 1 — Facing Direction vs Price

**Method:** Group by `facing`, compute `median(price_lakh)`, sort descending.

**Findings:**
- South-West: ₹97L (highest — location confound)
- North: ₹95L
- North-East: ₹89.8L
- East: ₹82L
- South: ₹50L

**Statistical nuance:** Median was used, not mean. Some facing directions have fewer than 100 properties — with small samples, a few outliers could distort the mean significantly. Median is robust to outliers.

**Key insight:** East-facing properties getting a premium partially supports Vastu theory. Morning sunlight (East) is practically desirable — natural light, lower summer heat in afternoons. The findings aren't purely superstitious — they align with livability preferences too.

---

## EDA 2 — Area Type vs Price Per Sqft

**Method:** Group by `areaWithType`, compute `median(price_per_sqft_numeric)`.

**Findings:**
- Plot Area: ₹6,481/sqft
- Super Area: ₹4,700/sqft
- Carpet Area: ₹4,657/sqft
- Built Area: ₹1,786/sqft

**Key insight for buyers:** Always ask for Carpet Area price. Super Area includes non-usable space (corridors, elevator shafts). A property quoted at ₹4,700/sqft on Super Area basis is actually closer to ₹5,500–6,500/sqft on Carpet Area — a ~30–40% difference.

---

## EDA 3 — New Property vs Resale

**Method:** Box plot comparison, `notched=True`.

**Findings:** New Property median ~₹1.065 Cr, Resale median ~₹55L.

**Why the gap is so large:**
1. New properties are typically being built in developing areas (Vesu, Pal, Adajan expansion zones) where land and construction costs are higher.
2. Builders include profit margin, GST, and RERA registration costs.
3. Resale properties include older inventory from 10–20 years ago, built when land was cheap.

---

## EDA 4 — Furnishing vs Price

**Method:** Group by `furnishing`, compute `median(price_lakh)`.

**Findings (counterintuitive):**
- Unfurnished: ₹84L
- Furnished: ₹65L
- Semi-Furnished: ₹46.25L

**The confounding variable explanation:** Large expensive assets (plots, industrial units, commercial offices) are always sold unfurnished. Their high prices pull the Unfurnished median up. Within the same property type (e.g., 2 BHK only), furnished would likely be priced higher. This is exactly the kind of nuanced interpretation that impresses interviewers.

---

## EDA 5 — Floor Level vs Price

**Method:** Parse floor string, bucket, compute `median(price_lakh)`.

**Findings:**
- Mid (4–8): ₹78L
- High (9+): ₹71L
- Low (1–3): lower
- Ground: lowest

**Why Ground is cheap:** Ground floor in India carries specific concerns: security vulnerability, dampness, lack of privacy from street level, and susceptibility to flooding. Premium ground floor units (garden apartments) are rare in Surat's market.

---

## EDA 6 — Property Size vs Price

**Method:** Bucketed analysis — Small (<1000 sqft), Medium (1000–2000), Large (2000–4000), Luxury (>4000). Scatter plot for continuous view.

**Findings:**
- Small: ₹34.1L median
- Medium: ₹66L
- Large: ₹1.55 Cr
- Luxury: ₹3.7 Cr

**Key insight:** Size is the single strongest predictor of price in this dataset. This is consistent with global real estate — square footage drives valuation more than any other single attribute.

---

## EDA 7 — Luxury Market Segmentation

**Method:** CASE WHEN binning in SQL, value_counts in Python, donut chart in Plotly.

**Findings:**
- Budget (<50L): 30.82%
- Mid-Range (50L–1Cr): 34.07%
- Premium (1Cr–2Cr): 21.07%
- Luxury (>2Cr): 18.10%

**Strategic reading:** Surat's market is bimodal — strong mid-market AND strong luxury. This is different from Tier-1 cities (Mumbai, Bangalore) where luxury dominates listings. Surat's manufacturing and diamond-trading economy creates a large middle class (Budget + Mid-Range) while the merchant class drives Luxury demand.

---

## EDA 8 — Top Premium Properties

**Method:** Sort by `sale_price` descending, filter for realistic values, examine top entries.

**Findings:**
- Industrial Shed: ₹55 Cr
- Commercial Land: ₹41 Cr
- Showroom: ₹31.5 Cr
- Office Space: ₹20 Cr

Residential luxury hotspots: Piplod, Rundh.

**Key insight:** The absolute top of the Surat market is dominated by commercial and industrial assets, not residential. This reflects Surat's identity as a manufacturing, diamond, and textile hub — industrial real estate carries enormous value.

---

## EDA 9 — Top 5 Most Expensive Property Types (by Median)

**Method:** Group by extracted category, compute median, sort, take top 5.

**Findings:**
- 5+ BHK: ₹3.5 Cr
- House: ₹2.5 Cr
- Showroom: ₹2.11 Cr
- 4 BHK: ₹1.9 Cr
- Industrial: ₹1 Cr

**Key insight:** The top-two are both residential — 5+ BHK and House. "House" typically means an independent bungalow with a plot, which explains the ₹2.5 Cr median (you're buying land + construction). Showroom's ₹2.11 Cr reflects high-footfall commercial strip demand in Surat's Ring Road and Adajan corridors.

---

# PART 5 — PROPERTY FINDER (Dashboard 3)

## Filter Logic

```python
if sel_cats:
    filtered = filtered[filtered["category"].isin(sel_cats)]
```

**Why `if sel_cats:` before filtering?**
An empty list `[]` is falsy in Python. If the user selects nothing, `sel_cats` is `[]`, the condition is `False`, and the filter is skipped — meaning "no selection = show all." Without this guard, `.isin([])` would return zero rows for every user who hasn't selected anything, breaking the entire finder.

```python
filtered = filtered[filtered["sale_price"].fillna(0) <= budget_range]
```

`.fillna(0)` ensures properties with no price (NaN) are treated as ₹0 and always pass the budget filter. This is intentional — "Call for Price" listings might still be within the user's budget; we want to surface them rather than hide them.

## Dynamic Metrics

```python
m1.metric("Matching Properties", f"{total_matches:,}")
m2.metric("Median Match Price", fmt_lakh(filtered["price_lakh"].median()))
m3.metric("Avg Match Area", f"{filtered['sqft_numeric'].median():,.0f} sqft")
```

These metrics update live as filters change. They give the user immediate feedback: "your filters found 23 properties with a median price of ₹85L." This is what makes the finder feel like a real product rather than a static table.

---

# PART 6 — VISUALIZATION TECHNIQUE SUMMARY

| Technique | Where Used | Why |
|---|---|---|
| Donut chart | Market Segmentation | Part-of-whole with centre annotation |
| Scatter plot with colour encoding | Size vs Price | Bivariate relationship + segment colouring |
| Horizontal bar + colour gradient | Category median price | Long category labels + value encoding |
| Notched box plot | New vs Resale | Full distribution + statistical confidence |
| Colour-categorised bar | Facing direction | Binary Vastu variable as colour |
| Floor-bucketed bar | Floor vs Price | Ordinal categorical, requires custom sort |
| Histogram | Property Finder | Frequency distribution of filtered results |
| KPI cards (custom HTML) | Executive Overview | Fast executive-level summary |
| `@st.cache_data` | Data loading | Performance — prevents re-computation |
| `pd.Categorical(ordered=True)` | Floor + Segment charts | Controls sort order of categorical axes |
| `on_bad_lines='skip'` | CSV loading | Handles malformed rows without crashing |
| Regex feature extraction | Property category | Structured data from unstructured text |
| `fillna(0)` before filter | Budget slider | Keeps NaN-priced rows in results |
| `**PLOTLY_LAYOUT` dict unpacking | All charts | DRY principle for consistent styling |
| Transparent bg (`rgba(0,0,0,0)`) | All charts | Charts blend into custom CSS background |
| `custom_data` in hover | Pie chart | Passes pre-calculated % into tooltip |
| `autorange='reversed'` | Category bar | Top-ranked item appears at top |
| 95th-percentile cap | Box plot | Removes visual distortion from outliers |

---

# PART 7 — KEY INTERVIEW PHRASES

These are clean, confident answers to common interview questions.

**"Walk me through your dashboard architecture."**
> "I built a 4-page Streamlit app using sidebar radio navigation. Page 1 is for executives — KPIs and macro market positioning. Page 2 is for buyers — it answers the 'where and what to buy' question. Page 3 is an interactive property finder. Page 4 is a SQL portfolio page targeting recruiters. The architecture mirrors a real analytics product: summary, exploration, search, technical showcase."

**"Why did you choose Streamlit over other tools?"**
> "Streamlit lets me write a data analytics dashboard entirely in Python — the same language I used for cleaning and EDA. There's no JavaScript, no separate frontend framework. It's ideal for a portfolio project because the code is readable, the deployment is simple, and it demonstrates Python skills end-to-end."

**"Why Plotly Express instead of Matplotlib?"**
> "Plotly produces interactive charts — users can hover, zoom, filter via legend clicks. For a real estate dashboard where someone might want to hover over a scatter point to see 'what property is this exactly,' interactivity adds genuine value. Matplotlib would produce a static PNG that's fine for a report but not for a live dashboard."

**"How did you handle data quality issues?"**
> "I had three layers of defence. First, SQL cleaned the source data — standardised facing directions, nulled invalid values, converted price strings to numeric. Second, on load I used `on_bad_lines='skip'` to handle a specific malformed row, and `to_numeric(errors='coerce')` to defensively re-cast numeric columns. Third, in the charts themselves I filter to `notna()` before groupby operations so nulls don't contaminate aggregations."

**"What was the most interesting finding in your EDA?"**
> "The furnishing status result. Intuitively you'd expect furnished properties to be more expensive. But unfurnished has the highest median price. The reason is a confounding variable — expensive assets like plots, industrial units, and commercial offices are always sold unfurnished. Within any single property type, furnished would likely be pricier. This is essentially Simpson's Paradox in a real estate context, and it's the kind of insight that separates analysis from just making charts."

---

*Surat Real Estate Analytics Platform — Interview Preparation Guide*
*Built with SQL · Python · Streamlit · Plotly*
