# HM-land-registry-data
Data analysis of HM Land Registry transactions

<code>HM-land-registry-datar</code> is a simple Python script that allows the user to analyze the large dataset from https://www.gov.uk/guidance/about-the-price-paid-data#download-options.

## How it works

The code is WIP. Currently there are several functionalities:


Loads the csv data downloaded from the gov website, converts it to pandas dataframe and adds headers.

Cleans the data by removing transactions which do not have postcodes (optional)

<code>add_latlon</code> functionality goes through all of the transactions and adds latitude and longitude for the property. This works with pgeocode Python library.

<code>type_sold</code> shows the type of properties sold historically with pie charts. T - Terraced, S - SemiDetached, D - Detached, F - Detached, F - Flat, O - Other.

<img src = "./doc_imag/type_sold.jpg">
