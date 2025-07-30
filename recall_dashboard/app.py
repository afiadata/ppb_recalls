import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os 
import altair as alt
import plotly.express as px
import io
st.set_page_config(
    page_title="Drug Recall Surveillance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Drug Recall Surveillance Dashboard")
# Load data

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'csv', 'recalls_combined.csv')
 
def load_data():
    df = pd.read_csv(DATA_PATH)

    #normalize column 
    df['manufacturer'] = df['manufacturer'].str.lower().str.strip()
    df['reason'] = df['reason'].str.lower().str.strip() 
    df['inn_name'] = df['inn_name'].astype(str).str.lower().str.strip()
    df['product_name'] = df['product_name'].astype(str).str.replace(r'\s+',' ', regex=True).str.strip().str.lower()

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    return df

df = load_data()

st.sidebar.header("Filter Recalls")

years = st.sidebar.multiselect(
    "Select Year(s)",
    options=df['year'].dropna().unique(),
    default=df['year'].dropna().unique()
)

manufacturers = st.sidebar.multiselect(
    "Select Manufacturer(s)",
    options=df['manufacturer'].dropna().unique(),
    default=df['manufacturer'].dropna().unique()
)

reasons = st.sidebar.multiselect(
    "Select Reason(s)",
    options=df['reason'].dropna().unique(),
    default=df['reason'].dropna().unique()
)


# Filter DataFrame based on selections
filtered_df = df[(df['year'].isin(years)) &
                 (df['manufacturer'].isin(manufacturers)) &
                 (df['reason'].isin(reasons))]

#Metrics
st.sidebar.subheader("Key Summary")
col1, col2, col3 = st.columns(3)

col1.metric("Total Recalls", len(filtered_df))
col2.metric("Unique Manufacturers", filtered_df['manufacturer'].nunique())
col3.metric("Unique Reasons", filtered_df['reason'].nunique())

#Time Series Analysis
st.subheader("Monthly Recall Trends")

monthly_counts = (
    filtered_df.groupby(['year', 'month'])
    .size()
    .reset_index(name='Recall Count')
    .sort_values(by=['year', 'month'])
)

monthly_counts["dtEpoch"] = pd.to_datetime(monthly_counts[['year', 'month']].assign(day=1))
monthly_counts.set_index("dtEpoch", inplace=True)

fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(
    data=monthly_counts,
    x='dtEpoch',
    y='Recall Count',
    marker='o',
    ax=ax
)
ax.set_title("Monthly Drug Recall Trends")
ax.set_xlabel("Date")
ax.set_ylabel("Number of Recalls")
st.pyplot(fig)

#Bar Chart: Top Recall Reasons
st.subheader("Top Recall Reasons")
top_reasons = (filtered_df['reason'].value_counts().nlargest(10)
               .sort_values(ascending=True))
fig2, ax = plt.subplots(figsize=(10, 6))
top_reasons.plot(kind='barh', ax=ax, color='skyblue')
ax.set_title("Top 10 Reasons for Drug Recalls")
ax.set_xlabel("Number of Recalls")
ax.set_ylabel("Reason")
st.pyplot(fig2)

# Altair Bar Chart: Recalls Per Year
st.subheader("Recalls Per Year (Altair Interactive View)")
alt_chart = (
    alt.Chart(filtered_df)
    .mark_bar()
    .encode(
        x=alt.X('year:O', title='Year'),
        y=alt.Y('count():Q', title='Number of Recalls'),
        tooltip=['year', 'count()']
    )
    .properties(width=700, height=400)
    .interactive()
)
st.altair_chart(alt_chart, use_container_width=True)

# Plotly Pie Chart: Recall Reasons Distribution
st.subheader("Recall Reasons Distribution (Plotly Pie Chart)")
reason_counts = filtered_df['reason'].value_counts().reset_index()
reason_counts.columns = ['reason', 'count']
fig_pie = px.pie(
    reason_counts,
    values='count',
    names='reason',
    title='Distribution of Recall Reasons',
    hole=0.4
)
fig_pie.update_traces(textinfo='percent+label')
st.plotly_chart(fig_pie, use_container_width=True)


st.subheader("Filtered Recalls Data")
st.dataframe(filtered_df, use_container_width=True)

#Export to excel
@st.cache_data
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered Recalls')
        
    return output.getvalue()

st.download_button(
    label="Download Filtered Data as Excel",
    data=convert_df_to_excel(filtered_df),
    file_name='filtered_recalls_data.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    key='download_excel'        
)




