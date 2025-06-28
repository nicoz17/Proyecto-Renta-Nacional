import pandas as pd
import numpy as np

def asignar_segmento(cotizante, df_segmentos):
    """
    Asigna el segmento correspondiente a un cotizante basado en las reglas definidas.
    
    Args:
        cotizante (dict): Diccionario con los datos del cotizante
        df_segmentos (pd.DataFrame): DataFrame con las reglas de segmentos.
    
    Returns:
        dict: Resultado de la asignación
    """
    mejor_segmento = None
    mejor_puntaje = 0
    motivo = ""
    
    for _, segmento in df_segmentos.iterrows():
        puntaje = 0
        razones = []
        
        # 1. Verificar tipo de renta (si existe en ambos)
        if 'TIPO_RENTA' in cotizante and 'TIPO_RENTA' in segmento and pd.notna(segmento['TIPO_RENTA']):
            if cotizante['TIPO_RENTA'] == segmento['TIPO_RENTA']:
                puntaje += 1
                razones.append(f"Tipo renta: {cotizante['TIPO_RENTA']}")
        
        # 2. Verificar rango de renta (si existe en ambos)
        rent_keys = ['RENTA', 'SALDO_MINIMO', 'SALDO_MAXIMO']
        if all(k in cotizante for k in ['RENTA']) and all(k in segmento for k in ['SALDO_MINIMO', 'SALDO_MAXIMO']):
            if pd.notna(segmento['SALDO_MINIMO']) and pd.notna(segmento['SALDO_MAXIMO']):
                if segmento['SALDO_MINIMO'] <= cotizante['RENTA'] <= segmento['SALDO_MAXIMO']:
                    puntaje += 2
                    razones.append(f"Renta {cotizante['RENTA']} en rango [{segmento['SALDO_MINIMO']}-{segmento['SALDO_MAXIMO']}]")
        
        # 3. Modalidad de renta (si existe en ambos)
        if 'MODALIDAD_RENTA' in cotizante and 'MODALIDAD_RENTA' in segmento and pd.notna(segmento['MODALIDAD_RENTA']):
            if cotizante['MODALIDAD_RENTA'] == segmento['MODALIDAD_RENTA']:
                puntaje += 1
                razones.append(f"Modalidad: {cotizante['MODALIDAD_RENTA']}")
        
        # 4. Meses garantizados (si existe en ambos)
        meses_keys = ['MESES_GARANTIZADOS', 'MESES_GARANTIZADOS_MINIMO', 'MESES_GARANTIZADOS_MAXIMO']
        if all(k in cotizante for k in ['MESES_GARANTIZADOS']) and all(k in segmento for k in ['MESES_GARANTIZADOS_MINIMO', 'MESES_GARANTIZADOS_MAXIMO']):
            if pd.notna(segmento['MESES_GARANTIZADOS_MINIMO']):
                min_val = segmento['MESES_GARANTIZADOS_MINIMO']
                max_val = segmento['MESES_GARANTIZADOS_MAXIMO'] if pd.notna(segmento['MESES_GARANTIZADOS_MAXIMO']) else float('inf')
                
                if min_val <= cotizante['MESES_GARANTIZADOS'] <= max_val:
                    puntaje += 1
                    razones.append(f"Meses garantizados: {cotizante['MESES_GARANTIZADOS']} en rango [{min_val}-{max_val}]")
        
        # Actualizar mejor segmento
        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_segmento = segmento['SEGMENTO']  # Nota: Verificar el nombre exacto de la columna!
            motivo = ", ".join(razones)
    
    return {
        'SEGMENTO_ASIGNADO': mejor_segmento,
        'MOTIVO': motivo,
        'COINCIDENCIA': mejor_puntaje
    }

def limpiar_datos(df):
    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.upper()
    
    # Convertir campos numéricos
    campos_numericos = ['RENTA', 'PRIMA_UNICA', 'MESES_GARANTIZADOS', 
                       'SALDO_MINIMO', 'SALDO_MAXIMO',
                       'MESES_GARANTIZADOS_MINIMO', 'MESES_GARANTIZADOS_MAXIMO']
    
    for campo in campos_numericos:
        if campo in df.columns:
            df[campo] = pd.to_numeric(df[campo], errors='coerce')
    
    # Rellenar NA con 0 solo para ciertos campos
    if 'MESES_GARANTIZADOS' in df.columns:
        df['MESES_GARANTIZADOS'].fillna(0, inplace=True)
    
    return df


import polars as pl

def contar_segmentos_polars(file_path, sheet_name=None):
    """
    Cuenta la cantidad de cotizaciones por segmento usando Polars.
    
    Args:
        file_path (str): Ruta al archivo Excel
        sheet_name (str, opcional): Nombre de la hoja a leer
    
    Returns:
        dict: Diccionario con {nombre_segmento: cantidad}
    """
    # Leer el archivo Excel
    if sheet_name:
        df = pl.read_excel(file_path, sheet_name=sheet_name)
    else:
        df = pl.read_excel(file_path)
    
    # Verificar si existe la columna necesaria
    if 'NOMBRE_SEGMENTO' not in df.columns:
        raise ValueError("El DataFrame no contiene la columna 'NOMBRE_SEGMENTO'")
    
    # Contar las ocurrencias de cada segmento
    conteo = (
        df.group_by('NOMBRE_SEGMENTO')
        .agg(pl.count().alias('cantidad'))
        .to_dict(as_series=False)
    )
    
    # Convertir a diccionario {nombre: cantidad}
    return dict(zip(conteo['NOMBRE_SEGMENTO'], conteo['cantidad']))

# Versión que retorna lista de tuplas
def contar_segmentos_polars_tuplas(file_path, sheet_name=None):
    """
    Devuelve una lista de tuplas con (segmento, cantidad) usando Polars.
    
    Args:
        file_path (str): Ruta al archivo Excel
        sheet_name (str, opcional): Nombre de la hoja a leer
        
    Returns:
        list: Lista de tuplas (nombre_segmento, cantidad)
    """
    if sheet_name:
        df = pl.read_excel(file_path, sheet_name=sheet_name)
    else:
        df = pl.read_excel(file_path)
    
    if 'NOMBRE_SEGMENTO' not in df.columns:
        raise ValueError("El DataFrame no contiene la columna 'NOMBRE_SEGMENTO'")
    
    return (
        df.group_by('NOMBRE_SEGMENTO')
        .agg(pl.count().alias('cantidad'))
        .rows()  # Esto devuelve lista de tuplas (segmento, cantidad)
    )

def cotizaciones_promedio(file_path, sheet_name=None):
    df = pl.read_excel(file_path)
    required_columns = {'COTIZANTE', 'COTIZACION'}
    
    max_por_cotizante = (
        df.group_by('COTIZANTE').agg(pl.max('COTIZACION').alias('MAX_COTIZACIONES')).sort('COTIZANTE')
    )
    return max_por_cotizante.mean()

if __name__ == "__main__":
    # testeo de conteo
    print("hola")
    conteo = contar_segmentos_polars('BBDD/SC_COTIZACIONES.xlsx')
    print("Conteo por segmento (diccionario):")
    for segmento, cantidad in conteo.items():
        print(f"{segmento}: {cantidad}")
    
    # Imprimir resultados
    print('promedio cotizaciones por cotizante')
    print(cotizaciones_promedio('BBDD/SC_COTIZACIONES.xlsx'))

    print("Conteo de cotizaciones por segmento:")
    for segmento, cantidad in conteo.items():
        print(f"{segmento}: {cantidad}")
    
    # Guardar en un archivo si es necesario
    with open('conteo_segmentos.txt', 'w') as f:
        for segmento, cantidad in conteo.items():
            f.write(f"{segmento}: {cantidad}\n")
    ###############################################
    # Cargar datos con hoja específica
    df_segmentos = pd.read_excel('BBDD/SC_SEGMENTOS.xlsx')  
    
    # Verificar columnas
    print("Columnas en df_segmentos:", df_segmentos.columns.tolist())
    
    # Limpiar datos
    df_segmentos = limpiar_datos(df_segmentos)
    
    # Ejemplo con un cotizante (ajustar a columnas reales)
    cotizante_ejemplo = {
        'RENTA': 750,
        'TIPO_RENTA': 'I',
        'MODALIDAD_RENTA': 'S',
        'MESES_GARANTIZADOS': 0
    }

    # Asignar segmento
    resultado = asignar_segmento(cotizante_ejemplo, df_segmentos)
    print("Resultado:", resultado)

    #TODO: Ahora que tenemos una forma de asignar
    # podemos simular personas --> asignarlas a segmentos