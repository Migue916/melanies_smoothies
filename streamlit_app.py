# Import python packages
import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col
 
# Conexión a Snowflake
cnx = st.connection("snowflake")
session = cnx.session()
 
# Consulta la tabla con columnas FRUIT_NAME y SEARCH_ON
my_dataframe = session.table('smoothies.public.fruit_options').select(
    col('FRUIT_NAME'),
    col('SEARCH_ON')
)
 
# Convertimos Snowpark DataFrame a pandas para usar .loc
pd_df = my_dataframe.to_pandas()
 
# Título de la app
st.title("🥤 Customize Your Smoothie! 🥤")
st.write("Choose the fruits you want in your custom Smoothie!")
 
# Nombre en la orden
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)
 
# Multiselect con límite de 5
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'],  # opciones visibles
    max_selections=5
)
 
# Si hay ingredientes seleccionados
if ingredients_list:
    ingredients_string = ''
 
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
 
        # Obtenemos el valor correcto para usar en la API
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
 
        # Título y llamada a la API
        st.subheader(fruit_chosen + ' Nutrition Information')
        try:
            fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
            fv_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)
        except:
            st.error(f"❌ Sorry, we couldn't find data for {fruit_chosen}.")
 
    # Botón para insertar la orden
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        insert_stmt = f"""
            insert into smoothies.public.orders (ingredients, name_on_order)
            values ('{ingredients_string.strip()}', '{name_on_order}')
        """
        session.sql(insert_stmt).collect()
        st.success(f"✅ Your Smoothie is ordered, {name_on_order}!")
