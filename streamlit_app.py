# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie!:cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom Smoothie!
    """
)

# Input for smoothie name
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch fruit options
my_dataframe = session.table('smoothies.public.fruit_options').select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert the Snowpark Dataframe to a Pandas DataFrame
pd_df = my_dataframe.to_pandas()
st.dataframe(pd_df)  # Display the table for reference

# Multi-select for ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Find the corresponding 'SEARCH_ON' value for the chosen fruit
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"The search value for {fruit_chosen} is {search_on}")

        # Fetch fruit nutrition information
        fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
        if fruityvice_response.status_code == 200:
            try:
                nutrition_data = fruityvice_response.json()
                st.subheader(f"{fruit_chosen} Nutrition Information")
                st.dataframe(data=nutrition_data, use_container_width=True)
            except ValueError:
                st.error(f"Error parsing JSON for {fruit_chosen}")
        else:
            st.error(f"Error fetching data for {fruit_chosen}: {fruityvice_response.status_code}")

    # SQL Insert Statement
    my_insert_stmt = f"""
    INSERT INTO smoothies.public.orders (ingredients, name_on_order)
    VALUES ('{ingredients_string.strip()}', '{name_on_order}');
    """
    st.write("Generated SQL Statement:")
    st.code(my_insert_stmt)

    # Submit Button
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
