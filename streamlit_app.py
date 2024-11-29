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

# Input for name
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Option to mark order as filled
order_filled = st.checkbox('Mark this order as filled', value=False)

# Establish Snowflake connection
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch fruit options
my_dataframe = session.table('smoothies.public.fruit_options').select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert Snowpark DataFrame to Pandas DataFrame
pd_df = my_dataframe.to_pandas()

# Display fruit options
st.dataframe(pd_df)

# Select fruits
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# Process selected ingredients
if ingredients_list:
    ingredients_string = ' '.join(ingredients_list)

    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        # Display nutrition information
        try:
            fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
            if fruityvice_response.status_code != 200:
                st.error(f"Error fetching data for {fruit_chosen}: {fruityvice_response.status_code}")
            else:
                fv_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)
        except Exception as e:
            st.error(f"An error occurred: {e}")
    
    # Generate SQL insert statement
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order, order_filled)
        VALUES ('{ingredients_string}', '{name_on_order}', {str(order_filled).upper()})
    """
    st.write(f"Generated SQL Statement:\n\n{my_insert_stmt}")

    # Submit button for order
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()
            st.success('Your Smoothie is ordered!', icon="✅")
        except Exception as e:
            st.error(f"An error occurred while inserting the order: {e}")
