import pandas as pd

# columnas -> lista de strings
def cleanmenosuno(file, columnas):
    # limpia los menos uno de alguna columna
    df = pd.read_excel(file, engine = 'openpyxl')
    for col in columnas:
        if col in df.columns:
            df = df[df[col] != -1]
        else:
            print("no esta la columna en el archivo")
            return None
    
    return df

# la gracia seria hacer un main que limpia los datos a nuestro gusto
#######
def main():
    archivo = 'FILE'
    columnas_a_limpiar = ['col1', 'col2']
    df = cleanmenosuno(archivo, columnas_a_limpiar)
    
    output = archivo.replace('.xlsx', '_output.csv')
    df.to_csv(output, index=False)
    return 1