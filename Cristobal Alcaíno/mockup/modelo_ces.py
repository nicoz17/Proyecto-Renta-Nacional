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

def procesar_y_exportar(ruta_archivo, directorio_salida = 'output'):
    os.makedirs(directorio_salida, exist_ok=True)

    try:
        df = pd.read_excel(ruta_archivo)
    except Exception as e:
        raise ValueError(f"Error al leer el archivo Excel {str(e)}")
    
    columnas_requeridas = ['FECHA_COTIZACION', 'COTIZANTE', 'NOMBRE_SEGMENTO']
    for col in columnas_requeridas:
        if col not in df.columns:
            raise ValueError(f"El archivo debe contener la columna: {col}")
    
    df["FECHA_COTIZACION"] = pd.to_datetime(df["FECHA_COTIZACION"])
    df = df.dropna(subset=["FECHA_COTIZACION", 'NOMBRE_SEGMENTO', 'COTIZANTE'])

    resultado = df.groupby(["FECHA_COTIZACION", 'NOMBRE_SEGMENTO'])['COTIZANTE'].nunique().unstack()
    nombre_archivo = 'series_por_segmento.pkl'

    resultado.to_pickle(f"{nombre_archivo}")
    return resultado

def obtener_serie_segmento_v2(pickle_name, segmento, fecha_inicio=None, fecha_fin=None):
    try:
        df = pd.read_pickle(pickle_name)
    except Exception:
        pass
    if segmento not in df.columns:
        raise ValueError
    
    serie = df[segmento]
    if fecha_inicio is not None or fecha_fin is not None:
        if fecha_inicio is not None and fecha_fin is not None:
            mask = (serie.index >= pd.to_datetime(fecha_inicio)) & (serie.index <= pd.to_datetime(fecha_fin))
        elif fecha_inicio is not None:
            mask = (serie.index >= pd.to_datetime(fecha_inicio))
        else:
            mask = (serie.index <= pd.to_datetime(fecha_fin))
        serie = serie.loc[mask]

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
        if False:
            procesar_y_exportar('BBDD/SC_COTIZACIONES.xlsx')
            print('procesando y exportando')
    except:
        pass
    
    # test para abrir el paquete de segmentos y buscar la serie temporal de algun segmento
    try:
        with open('segmentos_data.pkl', 'rb') as f:
            data, min_date, max_date = pickle.load(f)
        
        segmento_ejemplo = 'V 700-800 UF'
        if segmento_ejemplo in data:
            # esta funcion va a buscar un segmento como string en la data y retornar la serie de cotizaciones para los segmentos en el tiempo
            # esto hay que exportar
            # TODO: llamar a esta funcion en el main
            serie = obtener_serie_segmento(segmento_ejemplo, data, min_date, max_date)
            print(f"\n Serie temporal para '{segmento_ejemplo}':")
            print(serie.head())  
            print("\n Resumen estadístico:")
            print(serie.describe())

            # Predicción
            forecast = predict_auto_arima(serie, n_steps=14, m=1)
            print("\nPronóstico:")
            print(forecast)

            # Visualización
            plt.figure(figsize=(12, 6))
            serie.plot(label="Histórico", color='blue')
            forecast.plot(label="Pronóstico", color='orange')
            plt.legend()
            plt.title(f"{segmento_ejemplo}")
            plt.xlabel("Fecha")
            plt.ylabel("Cotizaciones ingresadas")
            plt.tight_layout()
            plt.show()
        else:
            print(f"{segmento_ejemplo} no esta lol")
    except:
        pass

    try:

        from statsmodels.tsa.seasonal import seasonal_decompose
        from statsmodels.tsa.filters.hp_filter import hpfilter
        from statsmodels.robust import mad
        from scipy.stats import boxcox, shapiro, normaltest
        from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
        from statsmodels.tsa.stattools import adfuller, kpss
        from pmdarima import auto_arima
        # 1. Obtención y preparación de datos
        serie_segmento = obtener_serie_segmento_v2(
            pickle_name='series_por_segmento.pkl', 
            segmento='V 700-800 UF', 
            fecha_inicio='2024-01-01', 
            fecha_fin='2024-06-02'
        ).asfreq('D').fillna(method='ffill')
        
        print(f"\nSerie temporal para '{segmento_ejemplo}':")
        print(serie_segmento.head())  
        print("\nResumen estadístico:")
        print(serie_segmento.describe())

        # 2. Preprocesamiento avanzado
        def preprocesar_serie(serie):
            # Manejo de outliers usando MAD
            median = serie.median()
            mad_score = mad(serie)
            serie_clean = serie.where(
                (serie - median).abs() < 3*mad_score,
                other=median
            )
            
            # Aplicar transformación Box-Cox
            from scipy.stats import boxcox
            transformed, _ = boxcox(serie_clean + 1)  # +1 para evitar ceros
            return pd.Series(transformed, index=serie.index)

        serie_procesada = preprocesar_serie(serie_segmento)

        # 3. Modelado mejorado
        def predict_auto_arima(series, n_steps):
            from pmdarima import auto_arima
            
            # Descomposición HP Filter
            cycle, trend = hpfilter(series, lamb=1600)
            
            # Modelado del componente cíclico
            model = auto_arima(
                cycle,
                seasonal=True,
                m=7,
                d=1,
                D=1,
                start_p=0,
                max_p=3,
                start_q=0,
                max_q=3,
                max_P=2,
                max_Q=2,
                trace=True,
                error_action='ignore',
                suppress_warnings=True,
                stepwise=True,
                information_criterion='aic',
                test='kpss',
                n_jobs=-1
            )
            
            # Pronóstico
            forecast_cycle = model.predict(n_periods=n_steps)
            forecast_dates = pd.date_range(
                start=series.index[-1] + pd.Timedelta(days=1),
                periods=n_steps
            )
            
            # Recombinar componentes
            return pd.Series(
                forecast_cycle + trend[-1],  # Ciclo + última tendencia
                index=forecast_dates,
                name='Pronóstico'
            ), model

        forecast, modelo = predict_auto_arima(serie_procesada, n_steps=14)
        
        # 4. Validación estadística mejorada
        def validar_modelo(model, series):
            residuos = model.resid()
            
            print("\n=== DIAGNÓSTICO AVANZADO ===")
            # Tests estadísticos
            from statsmodels.stats.diagnostic import het_arch, acorr_ljungbox
            from scipy.stats import shapiro, normaltest
            
            # Normalidad
            _, p_shapiro = shapiro(residuos)
            _, p_norm = normaltest(residuos)
            
            # Autocorrelación
            lb_test = acorr_ljungbox(residuos, lags=[10], return_df=True)
            
            # Heterocedasticidad
            _, p_arch, _, _ = het_arch(residuos)
            
            print(f"Normalidad - Shapiro: {'✅' if p_shapiro > 0.05 else '❌'} (p={p_shapiro:.4f})")
            print(f"Normalidad - D'Agostino: {'✅' if p_norm > 0.05 else '❌'} (p={p_norm:.4f})")
            print(f"Autocorrelación - Ljung-Box: {'✅' if lb_test["lb_pvalue"].values[0] > 0.05 else '❌'}")
            print(f"Heterocedasticidad - ARCH: {'✅' if p_arch > 0.05 else '❌'} (p={p_arch:.4f})")
            
            # Métricas de precisión
            from sklearn.metrics import mean_absolute_error, mean_squared_error
            train_pred = model.predict_in_sample()
            mae = mean_absolute_error(series, train_pred)
            rmse = np.sqrt(mean_squared_error(series, train_pred))
            
            print("\n=== MÉTRICAS DE AJUSTE ===")
            print(f"MAE: {mae:.2f}")
            print(f"RMSE: {rmse:.2f}")
            print(f"AIC: {model.aic():.2f}")
            print(f"BIC: {model.bic():.2f}")
            
            # Gráficos de diagnóstico
            fig, ax = plt.subplots(1, 2, figsize=(12, 4))
            model.plot_diagnostics()
            plt.tight_layout()
            plt.show()

        validar_modelo(modelo, serie_procesada)

        # 5. Visualización mejorada
        plt.figure(figsize=(14, 7))
        
        # Datos históricos
        plt.plot(serie_procesada.index, 
                serie_procesada.values, 
                label='Histórico Real', 
                color='#1f77b4',
                linewidth=2)
        
        # Pronóstico (inversa de Box-Cox si aplicó)
        plt.plot(forecast.index, 
                forecast.values, 
                label='Pronóstico', 
                color='#ff7f0e', 
                linestyle='--',
                linewidth=2)
        
        
        plt.title(f"Pronóstico para {segmento_ejemplo}\nCon validación estadística", pad=20)
        plt.xlabel("Fecha", labelpad=10)
        plt.ylabel("Cotizantes", labelpad=10)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        