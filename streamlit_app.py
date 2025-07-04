import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd # <--- ADD THIS IMPORT

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

cnx = st.connection("snowflake")
session = cnx.session()

# <--- IMPORTANT: Select both FRUIT_NAME and SEARCH_ON
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# <--- IMPORTANT: Convert Snowpark DataFrame to Pandas DataFrame BEFORE using it
pd_df = my_dataframe.to_pandas()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    options=pd_df['FRUIT_NAME'], # <--- Use the 'FRUIT_NAME' column from the Pandas DataFrame
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # <--- This line is now valid because pd_df is defined and has 'SEARCH_ON'
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        # st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')

        st.subheader(fruit_chosen + ' Nutrition Information')
        # Ensure 'requests' is imported if you haven't already (which you have)
        fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
        
        # Check if the API call was successful and data is available
        if fruityvice_response.status_code == 200:
            try:
                fv_data = fruityvice_response.json()
                # Ensure the JSON response is a list of dictionaries or a dictionary
                # that can be converted to a DataFrame. Some APIs return a single object,
                # which pandas.DataFrame can handle, but if it's a nested structure,
                # you might need to flatten it. For simplicity, we assume direct conversion.
                fv_df = pd.DataFrame([fv_data]) # Wrap in list if it's a single dict
                st.dataframe(fv_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error parsing nutrition data for {fruit_chosen}: {e}")
        else:
            st.warning(f"Could not fetch nutrition data for {fruit_chosen}. Status code: {fruityvice_response.status_code}")


    ingredients_string = ingredients_string.strip() # Remove trailing space

    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    # Ensure this button is only rendered once per run, not inside the loop
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        # Add a check for an empty name
        if not name_on_order:
            st.warning("Please enter your name for the smoothie order.")
        else:
            try:
                session.sql(my_insert_stmt).collect()
                st.success('Your Smoothie is ordered!', icon="✅")
            except Exception as e:
                st.error(f"Error processing your order: {e}")
