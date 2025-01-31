import streamlit as st
import pandas as pd
import plotly.express as px
import pgeocode
import openai
import os
from datetime import datetime

# ---------------------------- Streamlit Configuration ------------------------------- #
st.set_page_config(
    page_title="🏠 HM Land Registry AI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------- Load OpenAI API Key ------------------------------- #
openai.api_key = os.getenv("OPENAI_API_KEY")  # ✅ Set your API key in environment variables

# ---------------------------- Data Loading & Processing ------------------------------- #

@st.cache_data
def load_data(path):
    """Load the dataset."""
    try:
        df = pd.read_csv(path, header=None)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data
def assign_column_names(df):
    """Assign column names."""
    headers = [
        "id", "price", "date_of_transfer", "postcode", "property_type", "old_new",
        "duration", "paon", "saon", "street", "locality", "town_city",
        "district", "county", "ppd_category_type", "record_status"
    ]
    if df.shape[1] == len(headers):
        df.columns = headers
    return df

@st.cache_data
def clean_data(df):
    """Clean dataset by removing duplicates and ensuring datetime format."""
    df.drop_duplicates(inplace=True)
    df = df[df['postcode'].notna()]
    
    # ✅ Fix: Explicitly convert 'date_of_transfer' to datetime and print types for debugging
    df.loc[:, 'date_of_transfer'] = pd.to_datetime(df['date_of_transfer'], errors='coerce')

    # ✅ Print data types to verify
    st.write("🔍 Column Data Types After Cleaning:")
    st.write(df.dtypes)

    return df

@st.cache_data
def optimize_types(df):
    """Optimize data types for efficiency."""
    categorical_columns = ['property_type', 'old_new', 'duration', 'town_city', 'district', 'county']
    for col in categorical_columns:
        if col in df.columns:
            df[col] = df[col].astype('category')
    return df

@st.cache_data
def add_lat_lon(df):
    """Add latitude and longitude based on postcode."""
    nomi = pgeocode.Nominatim('gb')
    geocoded = nomi.query_postal_code(df['postcode'])
    df['latitude'] = geocoded['latitude'].fillna(0)
    df['longitude'] = geocoded['longitude'].fillna(0)
    return df

# ---------------------------- AI-Powered Querying ------------------------------- #

def query_openai(prompt):
    """Use OpenAI's GPT-4 to generate a Pandas query based on user input."""
    system_prompt = """
    You are an AI assistant that converts natural language questions into Python Pandas queries.
    The dataset contains UK real estate transactions with the following columns:
    - 'price': Property price in GBP.
    - 'date_of_transfer': Date of sale.
    - 'postcode': Postal code of the property.
    - 'property_type': (D: Detached, S: Semi-Detached, T: Terrace, F: Flats, O: Other)
    - 'town_city': City where the property is located.
    - 'county': County of the property.

    Examples:
    1. "What is the average price of flats in London?" → `df[df['property_type'] == 'F'][df['town_city'] == 'London']['price'].mean()`
    2. "Show the top 5 most expensive properties sold in Cambridge" → `df[df['town_city'] == 'Cambridge'].sort_values(by='price', ascending=False).head(5)`
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        # ✅ Fix: Extract response properly
        query_text = response.choices[0].message.content.strip()
        return query_text

    except Exception as e:
        return f"Error generating query: {str(e)}"

# ---------------------------- Main Dashboard ------------------------------- #

def main():
    st.title("🏠 HM Land Registry AI Dashboard")

    # Load and preprocess data
    data = load_data("datasets/pp-2024.csv")
    if data.empty:
        st.stop()
    
    data = assign_column_names(data)
    data = clean_data(data)
    data = optimize_types(data)
    data = add_lat_lon(data)

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    
    property_types = sorted(data['property_type'].unique())
    selected_property_types = st.sidebar.multiselect("Property Type", options=property_types, default=property_types)

    counties = sorted(data['county'].unique())
    selected_counties = st.sidebar.multiselect("County", options=counties, default=counties)

    min_date = data['date_of_transfer'].min().date()
    max_date = data['date_of_transfer'].max().date()
    selected_date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Apply Filters
    start_date, end_date = selected_date_range
    filtered_data = data[
        (data['property_type'].isin(selected_property_types)) &
        (data['county'].isin(selected_counties)) &
        (data['date_of_transfer'] >= pd.to_datetime(start_date)) &
        (data['date_of_transfer'] <= pd.to_datetime(end_date))
    ].copy()  # ✅ Fix: Ensures safe modifications

    # ✅ Fix: Ensure date_of_transfer is in datetime format
    filtered_data["date_of_transfer"] = pd.to_datetime(filtered_data["date_of_transfer"], errors="coerce")

    # ✅ Fix: AI Query Execution
    st.markdown("## 💬 Ask the AI")
    user_query = st.text_input("Type your question about UK property sales:")

    if user_query:
        generated_code = query_openai(user_query)
        
        # ✅ Fix: Strip backticks to prevent syntax errors
        generated_code = generated_code.strip("`")

        st.code(generated_code, language="python")

        try:
            local_vars = {"df": filtered_data, "pd": pd}
            result = eval(generated_code, {"__builtins__": {}}, local_vars)

            # ✅ Fix: Convert Series to DataFrame for better display
            if isinstance(result, pd.Series):
                result = result.to_frame().reset_index()

            st.write("### 📊 AI-Generated Query Result")
            st.dataframe(result)

        except Exception as e:
            st.error(f"Error executing query: {e}")

    # ✅ Price Trends Over Time
    price_trend = filtered_data.groupby('date_of_transfer', observed=False)['price'].mean().reset_index()
    st.line_chart(price_trend.set_index("date_of_transfer"))

    # ✅ Average Property Price by County
    avg_price = filtered_data.groupby("county", observed=False)["price"].mean().sort_values(ascending=False).head(20)
    st.bar_chart(avg_price)

    # ✅ Monthly Sales Trend
    filtered_data["month"] = filtered_data["date_of_transfer"].dt.to_period("M")
    monthly_sales = filtered_data.groupby("month", observed=False)["id"].count()
    st.line_chart(monthly_sales)

    # ✅ Price Distribution Histogram
    st.subheader("Property Price Distribution")
    st.plotly_chart(px.histogram(filtered_data, x="price", nbins=50, title="Price Distribution"))

    # ✅ Sales Volume by Property Type Over Time
    sales_by_type = filtered_data.groupby(["date_of_transfer", "property_type"], observed=False)["id"].count().reset_index()
    st.plotly_chart(px.area(sales_by_type, x="date_of_transfer", y="id", color="property_type", title="Sales by Property Type"))

    # 🔍 Data Preview
    st.dataframe(filtered_data.head(100))

if __name__ == "__main__":
    main()