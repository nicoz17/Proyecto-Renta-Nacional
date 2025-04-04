import pandas as pd

def cleanmenosuno(file, columna):
    # limpia los menos uno de alguna columna
    df = pd.read_excel(file, engine = 'openpyxl')
    df_filtrado = df[df[columna] != -1]
    output = file[:-4]+'output'
    df_filtrado.to_csv(output, index = False) 
    return None

# la gracia seria hacer un main que limpia los datos a nuestro gusto
#######