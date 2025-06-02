import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pmdarima import auto_arima
import os

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

if __name__ == "__test__":
    base_path = "BBDD"  # Ajusta si tu carpeta tiene otra ruta

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