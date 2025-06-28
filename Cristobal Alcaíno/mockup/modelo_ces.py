import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pmdarima import auto_arima
import os
import pickle
from collections import defaultdict
import time
import polars as pl

def cargar_datos(base_path):
    # Rutas a los archivos
    file_2024 = os.path.join(base_path, "SCOMP_MERCADO_2024.xlsx")
    file_2023 = os.path.join(base_path, "SCOMP_MERCADO_2024.xlsx")
    
    # Leer las hojas correspondientes
    df_2024 = pd.read_excel(file_2024, sheet_name="CES ING POR DIA", skiprows=2)
    df_2023 = pd.read_excel(file_2023, sheet_name="CES ING POR DIA", skiprows=2)
    
    # Extraer columnas relevantes
    ces_2023 = df_2023['CES.Ingresados']
    ces_2024 = df_2024['CES.Ingresados']
    
    fechas_2023 = df_2023['Fecha.Recepcion.CES']
    fechas_2024 = df_2024['Fecha.Recepcion.CES']
    
    # Convertir fechas a formato datetime
    fechas_2023 = pd.to_datetime(fechas_2023, format='%d/%m/%y', errors='coerce')
    fechas_2024 = pd.to_datetime(fechas_2024, format='%d/%m/%y', errors='coerce')
    
    # Unir datos de ambos años
    ces = pd.concat([ces_2023, ces_2024], ignore_index=True)
    fechas = pd.concat([fechas_2023, fechas_2024], ignore_index=True)
    
    # Crear DataFrame y agrupar por fecha
    df = pd.DataFrame({'Fecha': fechas, 'CES': ces})
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # Agrupar por fecha y sumar CES
    serie_diaria = df.groupby('Fecha')['CES'].sum().reset_index()
    
    # Crear rango completo de fechas
    fecha_min = serie_diaria['Fecha'].min()
    fecha_max = serie_diaria['Fecha'].max()
    fechas_completas = pd.date_range(start=fecha_min, end=fecha_max, freq='D')
    
    # Crear serie completa rellenando días faltantes con 0
    serie_completa = pd.DataFrame({'Fecha': fechas_completas})
    serie_completa = pd.merge(serie_completa, serie_diaria, on='Fecha', how='left')
    serie_completa['CES'].fillna(0, inplace=True)
    
    # Convertir a serie temporal diaria
    ts_diaria = serie_completa.set_index('Fecha')['CES']
    
    return ts_diaria

# TODO: Construir serie de tiempo para un j-segmento tal que en k dias prediga que van a llegar m cotizaciones
def cargar_datos_segmentos(base_path):
    # TODO: inicializar set de segmentos?
    # TODO: Cargar datos, guardar fecha, conteo segmento
    # TODO: generar la tupla (fecha, segmento, solicitudes de ese dia)
    # TODO: retornar el arima
    pass

def procesar_datos_segmentos(archivo_excel, output_path='segmentos_data.pkl', chunk_size=1000):
    df = pd.read_excel(archivo_excel, usecols=['FECHA_COTIZACION', 'NOMBRE_SEGMENTO'], parse_dates=['FECHA_COTIZACION'])
    df = df.dropna(subset=['FECHA_COTIZACION', 'NOMBRE_SEGMENTO'])
    df['fecha'] = df['FECHA_COTIZACION'].dt.date

    print('contando ocurrencias')
    conteos = df.groupby(['NOMBRE_SEGMENTO', 'fecha']).size().reset_index(name='conteo')
    segmentos_data = defaultdict(dict)
    for _, row in conteos.iterrows():
        segmentos_data[row['NOMBRE_SEGMENTO']][row['fecha']] = row['conteo']
    
    min_date = df['fecha'].min()
    max_date = df['fecha'].max()

    with open(output_path, 'wb') as f:
        pickle.dump((dict(segmentos_data), min_date, max_date), f)
    
    print(f"Datos procesados y guardados en {output_path}")
    print(f'Rango de fechas {min_date} a {max_date}')
    print(f"segmentos unicos {len(segmentos_data)}")

    return segmentos_data, min_date, max_date

def obtener_serie_segmento(segmento, segmentos_data, min_date, max_date):
                datos_segmento = segmentos_data.get(segmento, {})
                rango_fechas = pd.date_range(start=min_date, end=max_date, freq='D')
                serie = pd.Series(
                    index=rango_fechas, 
                    data=[datos_segmento.get(fecha.date(), 0) for fecha in rango_fechas] 
                )
                return serie


def predict_auto_arima(ts, n_steps=14, seasonal=False, m=1):
    """Esta funcion hace un autoarima general de una serie de tiempo que le pasamos"""
    model = auto_arima(ts,
                       seasonal=seasonal,
                       m=m,
                       stepwise=True,
                       suppress_warnings=True,
                       error_action='ignore')
    
    forecast = model.predict(n_periods=n_steps)
    return pd.Series(forecast, index=pd.date_range(ts.index[-1] + pd.Timedelta(days=1), periods=n_steps, freq='D'))

#reemplazar main 

if __name__ == "__main__":
    base_path = "BBDD"  
     
    # test de la serie de tiempo de cotizantes
    try:
        ts = cargar_datos(base_path)
        print("Serie cargada correctamente:")
        print(ts.tail())

        # Predicción
        forecast = predict_auto_arima(ts, n_steps=14)
        print("\nPronóstico:")
        print(forecast)

        # Visualización
        plt.figure(figsize=(12, 6))
        ts.plot(label="Histórico", color='blue')
        forecast.plot(label="Pronóstico", color='orange')
        plt.legend()
        plt.title("Pronóstico de CES con Auto ARIMA")
        plt.xlabel("Fecha")
        plt.ylabel("CES ingresados")
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error al ejecutar el script: {e}")

    # test de segmentos
    try:
        if False:
            data, min_date, max_date = procesar_datos_segmentos(archivo_excel='BBDD/SC_COTIZACIONES.xlsx',
                                                            chunk_size=10000)
        # test de esto  
        pass
    except:
        pass
    
    # test para abrir el paquete de segmentos y buscar la serie temporal de algun segmento
    try:
        with open('segmentos_data.pkl', 'rb') as f:
            data, min_date, max_date = pickle.load(f)
        
        segmento_ejemplo = 'V 700-800 UF'
        if segmento_ejemplo in data:
            # esta funcion va a buscar un segmento como string en la data y retornar la serie
            # esto hay que exportar
            # TODO: llamar a esta funcion en el main
            
            serie = obtener_serie_segmento(segmento_ejemplo, data, min_date, max_date)
            print(f"\n Serie temporal para '{segmento_ejemplo}':")
            print(serie.head())  
            print("\n Resumen estadístico:")
            print(serie.describe())

            # Predicción
            forecast = predict_auto_arima(ts, n_steps=14)
            print("\nPronóstico:")
            print(forecast)

            # Visualización
            plt.figure(figsize=(12, 6))
            ts.plot(label="Histórico", color='blue')
            forecast.plot(label="Pronóstico", color='orange')
            plt.legend()
            plt.title(f"{segmento_ejemplo}")
            plt.xlabel("Fecha")
            plt.ylabel("CES ingresados")
            plt.tight_layout()
            plt.show()

        else:
            print(f"{segmento_ejemplo} no esta lol")
    except:
        pass