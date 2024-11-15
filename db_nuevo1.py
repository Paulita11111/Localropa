import sqlite3
import requests
import pandas as pd
from flask import Flask, jsonify, request

DATABASE = "base1.db"
CSV_FILE = "Updated_Clothing_Products.csv"  # Usando el archivo descargado

# Función para crear la tabla en la base de datos
def crear_tabla():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS product_catalog')
        c.execute(''' 
            CREATE TABLE IF NOT EXISTS product_catalog (
                "index" INTEGER,
                product TEXT,
                category TEXT,
                sub_category TEXT,
                brand TEXT,
                sale_price REAL,
                market_price REAL,
                type TEXT,
                rating REAL,
                description TEXT,
                sale_price_euro REAL,
                market_price_euro REAL
            )
        ''')
        conn.commit()

# Función para importar los productos desde el CSV
def importar_productos():
    try:
        df = pd.read_csv(CSV_FILE, on_bad_lines='skip', delimiter=",")
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            for _, row in df.iterrows():
                c.execute(''' 
                    INSERT INTO product_catalog (
                        "index", product, category, sub_category, brand, sale_price, 
                        market_price, type, rating, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row["index"], row["product"], row["category"], row["sub_category"],
                    row["brand"], row["sale_price"], row["market_price"], 
                    row["type"], row["rating"], row["description"]
                ))
            conn.commit()
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")

# Función para obtener todos los productos
def get_products():
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        products = conn.execute("SELECT * FROM product_catalog").fetchall()
        return products

# Función para obtener un producto por su ID
def get_product(id):
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        product = conn.execute("SELECT rowid, * FROM product_catalog WHERE rowid = ?", (id,)).fetchone()
        if product is None:
            return {"message": "Product not found"}, 404
        return dict(product)

# Función para añadir un nuevo producto
def add_product(new_product):
    #new_product = request.get_json()
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(''' 
            INSERT INTO product_catalog (
                "index", product, category, sub_category, brand, sale_price, 
                market_price, type, rating, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_product['index'], new_product['product'], new_product['category'], 
            new_product['sub_category'], new_product['brand'], new_product['sale_price'], 
            new_product['market_price'], new_product['type'], new_product['rating'], 
            new_product['description']
        ))
        conn.commit()

# Función para actualizar un producto existente
def update_product(id):
    product_details = request.get_json()
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(''' 
            UPDATE product_catalog SET 
                "index" = ?, product = ?, category = ?, sub_category = ?, brand = ?, 
                sale_price = ?, market_price = ?, type = ?, rating = ?, description = ?
            WHERE rowid = ?
        ''', (
            product_details['index'], product_details['product'], product_details['category'], 
            product_details['sub_category'], product_details['brand'], product_details['sale_price'], 
            product_details['market_price'], product_details['type'], product_details['rating'], 
            product_details['description'], id
        ))
        conn.commit()

# Función para eliminar un producto
def delete_product(id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("DELETE FROM product_catalog WHERE rowid = ?", (id,))
        conn.commit()

# Función para obtener el valor del dólar en euros
def obtener_valores_dolar():
    base_url = "https://dolarapi.com/v1/cotizaciones/"
    currency = "eur"
    url = f"{base_url}{currency}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        venta = data.get("venta")
        if venta:
            return venta
        else:
            print("Error: 'venta' no encontrado en la respuesta de la API")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener los datos de la API: {e}")
        return None

# Función para convertir la base de datos a DataFrame
def db_to_dataframe():
    try:
        with sqlite3.connect(DATABASE) as conn:
            # Leemos todos los productos de la tabla en un DataFrame
            df = pd.read_sql_query("SELECT rowid, * FROM product_catalog", conn)
        return df
    except Exception as e:
        print(f"Error al convertir la base de datos a DataFrame: {e}")
        return None

# Función para mostrar el DataFrame
def mostrar_dataframe():
    df = db_to_dataframe()
    if df is not None:
        print("Contenido de la base de datos:")
        print(df)  # Mostrar el DataFrame
    else:
        print("No se pudo convertir la base de datos a DataFrame.")



# Función principal para inicializar la base de datos y la importación de productos
def iniciar():
    try:
        crear_tabla()
        importar_productos()
        print("Database and table creation successful, and products imported.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Menú interactivo
def menu_interactivo():
    textoMenu = """
    Ingrese una opción:
    1. Crear tablas
    2. Importar productos desde CSV
    3. Consultar todos los productos
    4. Consultar un producto por ID
    5. Añadir un nuevo producto
    6. Actualizar un producto existente
    7. Eliminar un producto
    8. Mostrar productos con precios en euros
    9. Mostrar productos como DataFrame
    0. Salir
    """
    opcion = -1
    while opcion != 0:
        print(textoMenu)
        try:
            opcion = int(input("Seleccione una opción: "))
            if opcion == 1:
                crear_tabla()
            elif opcion == 2:
                importar_productos()
            elif opcion == 3:
                products = get_products()
                for product in products:
                    print(dict(product))
            elif opcion == 4:
                id = int(input("Ingrese el ID del producto: "))
                product = get_product(id)
                print(product)
            elif opcion == 5:
                add_product()
            elif opcion == 6:
                id = int(input("Ingrese el ID del producto a actualizar: "))
                update_product(id)
            elif opcion == 7:
                id = int(input("Ingrese el ID del producto a eliminar: "))
                delete_product(id)
            elif opcion == 8:
                euro_rate = obtener_valores_dolar()
                if euro_rate:
                    with sqlite3.connect(DATABASE) as conn:
                        conn.execute(''' 
                            UPDATE product_catalog
                            SET sale_price_euro = sale_price * ?, 
                                market_price_euro = market_price * ?
                        ''', (euro_rate, euro_rate))
                        conn.commit()
                    products = get_products()
                    for product in products:
                        print(product)
            elif opcion == 9:
                mostrar_dataframe()  # Llamamos a la nueva función para mostrar el DataFrame
            elif opcion == 0:
                print("Saliendo...")
            else:
                print("Opción no válida.")
        except ValueError:
            print("Ingrese un número válido.")


if __name__ == "__main__":
    iniciar()
    menu_interactivo()
