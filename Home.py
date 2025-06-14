#───────────────────────────────────────────────────────────────────────
# Cardiovascular-Disease Dashboard  ·  Streamlit inside Colab
#───────────────────────────────────────────────────────────────────────
# 0️⃣  Upload CSV
from google.colab import files, output
import pandas as pd, numpy as np, textwrap, os, threading, time, json
upload = files.upload()                       # choose your CSV
csv_bytes = list(upload.values())[0]          # first (and only) file content
df = pd.read_csv(pd.compat.StringIO(csv_bytes.decode()))

# 1️⃣  Quick cleaning
df["date"]       = pd.to_datetime(df["year_month"], errors="coerce")
df["year"]       = df["date"].dt.year
df["month"]      = df["date"].dt.month
df["residence"]  = df["residence"].fillna("Unknown")
df["sex"]        = df["sex"].replace({"UNKNOWN": "Unknown"})
df["age_band"]   = df["age_band"].replace({"Unknown": "0. Unknown"})
df.to_pickle("df_clean.pkl")                  # Streamlit will read this

# 2️⃣  Install once (will be skipped next runs if already present)
!pip install --quiet streamlit plotly

# 3️⃣  Write the Streamlit app
APP = '''
import streamlit as st, pandas as pd, plotly.express as px
st.set_page_config(page_title="CVD Dashboard", layout="wide")
st.title("📊 Cardiovascular-Disease Trends in Lebanon (2019-2023)")

df = pd.read_pickle("df_clean.pkl")

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filters")
    year  = st.multiselect("Year", sorted(df.year.dropna().unique()), default=sorted(df.year.dropna().unique()))
    sex   = st.multiselect("Sex",  df.sex.unique(),  default=list(df.sex.unique()))
    age   = st.multiselect("Age band", df.age_band.unique(), default=list(df.age_band.unique()))
    res   = st.multiselect("Residence", df.residence.unique(), default=list(df.residence.unique()))
flt = df[df.year.isin(year) & df.sex.isin(sex) & df.age_band.isin(age) & df.residence.isin(res)]

# KPIs
c1, c2 = st.columns(2)
c1.metric("Total cases", int(flt.cvd_cases.sum()))
c2.metric("Distinct locations", flt.residence.nunique())

# Monthly trend
ts = flt.groupby("date").cvd_cases.sum().reset_index()
st.plotly_chart(px.line(ts, x="date", y="cvd_cases", title="Monthly CVD cases"), use_container_width=True)

# Top 10 locations
top10 = flt.groupby("residence").cvd_cases.sum().nlargest(10).reset_index()
fig = px.bar(top10, x="cvd_cases", y="residence", orientation="h", title="Top 10 Locations", text="cvd_cases")
fig.update_layout(yaxis=dict(categoryorder="total ascending"))
st.plotly_chart(fig, use_container_width=True)

# Sex & Age distributions
c3, c4 = st.columns(2)
c3.plotly_chart(px.pie(flt, names="sex", values="cvd_cases", title="Cases by Sex"), use_container_width=True)
age_dist = flt.groupby("age_band").cvd_cases.sum().reset_index()
c4.plotly_chart(px.bar(age_dist, x="age_band", y="cvd_cases", title="Cases by Age Band"), use_container_width=True)

st.caption("Draft dashboard for MSBA350 Healthcare Analytics project")
'''
open("cvd_app.py", "w").write(textwrap.dedent(APP))

# 4️⃣  Launch Streamlit
PORT = 8501
def run_app(): os.system(f"streamlit run cvd_app.py --server.headless true --server.port {PORT}")
threading.Thread(target=run_app, daemon=True).start()
time.sleep(7)
print("🚀  Dashboard link:", output.eval_js(f"google.colab.kernel.proxyPort({PORT})"))
