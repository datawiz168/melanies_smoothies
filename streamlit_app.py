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

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch data from Snowflake table
my_dataframe = session.table('smoothies.public.fruit_options').select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()
st.dataframe(pd_df)

# Allow user to select fruits
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Handle API call with error handling
        try:
            search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
            fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
            
            if fruityvice_response.status_code != 200:
                st.error(f"Error fetching data for {fruit_chosen}: {fruityvice_response.status_code}")
            else:
                st.subheader(fruit_chosen + ' Nutrition Information')
                fv_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)
        except Exception as e:
            st.error(f"An error occurred while fetching data for {fruit_chosen}: {e}")
    
    # Add a checkbox for 'filled' status
    is_filled = st.checkbox('Mark this order as filled')
    
    # Generate SQL statement
    my_insert_stmt = f"""INSERT INTO smoothies.public.orders (ingredients, name_on_order, is_filled)
            VALUES ('{ingredients_string.strip()}', '{name_on_order}', {is_filled});"""
    
    st.write("Generated SQL Statement:")
    st.code(my_insert_stmt)
    
    # Add a button to submit the order
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()
            st.success('Your Smoothie is ordered!', icon="✅")
        except Exception as e:
            st.error(f"An error occurred while inserting the order: {e}")
