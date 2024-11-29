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

# 输入 Smoothie 名称
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# 连接到 Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# 查询数据并转为 Pandas DataFrame
my_dataframe = session.table('smoothies.public.fruit_options').select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

# 显示 Pandas 数据框供参考
st.dataframe(pd_df, use_container_width=True)

# 显示水果选择器
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df['FRUIT_NAME'].tolist(),  # 提供水果名称作为选项
    max_selections=5
)

# 处理用户选择的水果
if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        # 拼接选择的水果名称
        ingredients_string += fruit_chosen + ' '
        
        # 获取对应的搜索关键字
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f'The search value for {fruit_chosen} is {search_on}')
        
        # 调用 Fruityvice API 获取营养信息
        fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
        if fruityvice_response.status_code == 200:
            nutrition_data = fruityvice_response.json()
            st.subheader(f"{fruit_chosen} Nutrition Information")
            st.dataframe(data=nutrition_data, use_container_width=True)
        else:
            st.error(f"Error fetching data for {fruit_chosen}")

    # 构造 SQL 插入语句
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}');
    """
    st.write("Generated SQL Statement:")
    st.code(my_insert_stmt)

    # 添加提交按钮
    if st.button('Submit Order'):
        try:
            session.sql(my_insert_stmt).collect()
            st.success('Your Smoothie is ordered!', icon="✅")
        except Exception as e:
            st.error(f"Error submitting order: {e}")
