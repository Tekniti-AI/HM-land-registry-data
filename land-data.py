import pandas as pd
import numpy as np
import plotly
import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import pgeocode

# ---------------------------- Load in HM Land Registry Data ------------------------------- #

# Data and data description can be found here: https://www.gov.uk/guidance/about-the-price-paid-data#download-options

data = pd.read_csv("datasets/pp-2024.csv")
headers = ["id", "price", "date_of_transfer", "postcode", "property_type", "old_new", "duration", "paon", "saon",
           "street", "locality", "town_city", "district", "county", "ppd_caterogy_type", "record_status"]
data.columns = headers

pd.options.display.float_format = '{:,.2f}'.format

# ---------------------------- Clean and review the data ------------------------------- #
print(data)
print(data.describe())
print(f'Any NaN values? {data.isna().values.any()}')
print(f'Any duplicates? {data.duplicated().values.any()}')

# Remove any transactions without postcode
data = data[data['postcode'].notna()]


# ---------------------------- Add latitude and longitude with pgeocode ------------------------------- #

def add_latlon(dataset, filename):
    nomi = pgeocode.Nominatim('gb')
    for index, row in dataset.iterrows():
        try:
            data.loc[index, 'latitude'] = nomi.query_postal_code(data['postcode'][index])['latitude']
            data.loc[index, 'longitude'] = nomi.query_postal_code(data['postcode'][index])['longitude']
            print(
                f"Post code:{data['postcode'][index]} | lat: {data['latitude'][index]} | lon: {data['latitude'][index]}")
        except:
            data.loc[index, 'latitude'] = 0
            data.loc[index, 'longitude'] = 0

    data.to_csv(filename)


# ---------------------------- Functions to generate graphs ------------------------------- #

def type_sold():
    types = data.property_type.value_counts()
    fig = px.pie(labels=types.index,
                 values=types.values,
                 title="Type of properties sold",
                 names=types.index,
                 hole=0.4, )

    fig.update_traces(textposition='inside', textfont_size=15, textinfo='percent')
    plotly.offline.plot(fig, filename="type_sold.html")


def sold_location():
    locations = data.county.value_counts()
    fig = px.pie(labels=locations.index,
                 values=locations.values,
                 title="Properties sold per location",
                 names=locations.index,
                 hole=0.4, )

    fig.update_traces(textposition='inside', textfont_size=15, textinfo='percent')
    plotly.offline.plot(fig, filename="sold_location.html")


def sales_per_category():
    sells_per_category = data.property_type.value_counts()
    v_bar = px.bar(
        x=sells_per_category.index,
        y=sells_per_category.values,
        color=sells_per_category.values,
        color_continuous_scale='Aggrnyl',
        title='Number of sales per category')

    v_bar.update_layout(xaxis_title='Terrace/SemiDetached/Detached/Flat/Other',
                        coloraxis_showscale=False,
                        yaxis_title='Number of Sales')
    plotly.offline.plot(v_bar, filename="sales_per_category.html")


def top_20_cities():
    top20_cities = data.town_city.value_counts()[:20]
    top20_cities.sort_values(ascending=True, inplace=True)

    top20c = px.bar(x=top20_cities.values,
                    y=top20_cities.index,
                    orientation='h',
                    color=top20_cities.values,
                    color_continuous_scale=px.colors.sequential.haline,
                    title='Top 20 Cities and Towns by Number of Sales')

    top20c.update_layout(xaxis_title='Number of Sales',
                         yaxis_title='City/Town',
                         coloraxis_showscale=False)
    plotly.offline.plot(top20c, filename="top20_city.html")


def top_20_county():
    top20_cities = data.county.value_counts()[:20]
    top20_cities.sort_values(ascending=True, inplace=True)

    top20county = px.bar(x=top20_cities.values,
                         y=top20_cities.index,
                         orientation='h',
                         color=top20_cities.values,
                         color_continuous_scale=px.colors.sequential.haline,
                         title='Top 20 Counties by Number of Sales')

    top20county.update_layout(xaxis_title='Number of Sales',
                              yaxis_title='City/Town',
                              coloraxis_showscale=False)
    plotly.offline.plot(top20county, filename="top20_county.html")


def bottom_20_cities():
    bottom20_cities = data.town_city.value_counts()[::-20]
    bottom20_cities.sort_values(ascending=True, inplace=True)

    bottom20c = px.bar(x=bottom20_cities.values,
                       y=bottom20_cities.index,
                       orientation='h',
                       color=bottom20_cities.values,
                       color_continuous_scale=px.colors.sequential.haline,
                       title='Bottom 20 Cities and Towns by Number of Sales')

    bottom20c.update_layout(xaxis_title='Number of Sales',
                            yaxis_title='City/Town',
                            coloraxis_showscale=False)
    plotly.offline.plot(bottom20c, filename="bottom20_cities.html")


def bottom_20_county():
    bottom20_county = data.county.value_counts()[::-20]
    bottom20_county.sort_values(ascending=True, inplace=True)

    bottom20county = px.bar(x=bottom20_county.values,
                            y=bottom20_county.index,
                            orientation='h',
                            color=bottom20_county.values,
                            color_continuous_scale=px.colors.sequential.haline,
                            title='Bottom 20 Counties by Number of Sales')

    bottom20county.update_layout(xaxis_title='Number of Sales',
                                 yaxis_title='City/Town',
                                 coloraxis_showscale=False)
    plotly.offline.plot(bottom20county, filename="bottom20_county.html")


def location_sunburst():
    county_district_city = data.groupby(by=['county',
                                            'district',
                                            'town_city'], as_index=False).agg({'price': pd.Series.count})

    county_district_city = county_district_city.sort_values('price', ascending=False)

    burst = px.sunburst(county_district_city,
                        path=['county', 'district', 'town_city'],
                        values='price',
                        title='Where did transactions take place?',
                        )

    burst.update_layout(xaxis_title='Number of Transactions',
                        yaxis_title='date_of_transfer',
                        coloraxis_showscale=False)

    plotly.offline.plot(burst, filename="location_burst.html")

# ---------------------------- Use functions from above to generate graphs ------------------------------- #
