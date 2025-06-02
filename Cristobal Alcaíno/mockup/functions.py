import random
import pandas as pd
import os
import pickle
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
from sklearn.metrics import silhouette_score

# Visualiza los clusters de segundo nivel
# Función que simula probabilidades en función de la tasa
#TODO: Usar los argumentos en la funcion
def unir_cotizaciones(bbdd1, bbdd2, base_path='BBDD'):
    """funcion que une 2 xlsx sobre la misma columna COTIZACIONES
    retorna el .xlsx"""
    ## TODO: limpiar duplicados, limpiar rechazos, limpiar invalidos
    ## TODO: Pedirle estos archivos a NICO B. o verificar cuales son
    # TODO: Insertar los argumentos aca
    cotizaciones = pd.read_excel(os.path.join(base_path, bbdd1))
    sc_cotizaciones = pd.read_excel(os.path.join(base_path, bbdd2))
    
    ids_con_aceptada = cotizaciones[cotizaciones['ACEPTADA']==1]['COTIZANTE'].unique()
    cotizaciones['ACEPTADA'] = cotizaciones['ACEPTADA'].replace(-1, 1)

    filtro = (
        (cotizaciones['COTIZANTE'].isin(ids_con_aceptada)) & 
        (cotizaciones['ACEPTADA'] == 1) &
        (cotizaciones['TIPO_RENTA'] == "I") &
        (cotizaciones['MODALIDAD_RENTA'] == "G")
    ) | (
        (~cotizaciones['COTIZANTE'].isin(ids_con_aceptada)) &
        (cotizaciones['TIPO_RENTA'] == "I") &
        (cotizaciones['MODALIDAD_RENTA'] == "G")
    )

    datos_filtrados = cotizaciones[filtro]
    sc_cotizaciones = pd.read_excel(os.path.join(base_path, bbdd2))

    datos_filtrados_con_posicion = pd.merge(
        datos_filtrados,
        sc_cotizaciones[['COTIZANTE', 'COTIZACION', 'POSICION_RELATIVA']],
        on=['COTIZANTE', 'COTIZACION'],
        how='left'
    )

    datos_filtrados_con_posicion['POSICION_RELATIVA'] = pd.to_numeric(
    datos_filtrados_con_posicion['POSICION_RELATIVA'],
    errors='coerce'
    )

    columnas_numericas = datos_filtrados_con_posicion.select_dtypes(include=np.number).columns
    numericas = datos_filtrados_con_posicion[columnas_numericas]

    aceptada_var = numericas['ACEPTADA']
    numericas_sin_constantes = numericas.loc[:, numericas.nunique() > 1]

    if 'POSICION_RELATIVA' not in numericas_sin_constantes.columns:
        numericas_sin_constantes['POSICION_RELATIVA'] = datos_filtrados_con_posicion['POSICION_RELATIVA']
        print("POSICION_RELATIVA fue agregada manualmente porque fue eliminada en el filtrado.")

    if 'ACEPTADA' not in numericas_sin_constantes.columns:
        numericas_sin_constantes['ACEPTADA'] = aceptada_var
    datos_modelo = numericas_sin_constantes.dropna()
    ## hey en vola podria retornar el pickle
    return datos_modelo

def guardar_como_picke(objeto, ruta):
    with open(ruta, 'wb') as f:
        pickle.dump(objeto, f)

def cargar_desde_pickle(ruta):
    with open(ruta, 'rb') as f:
        return pickle.load(f)

# TODO: Revisar este codigo
def estimar_probabilidades_ranking(tasa):
    """tasa: float
    Retorna la probabilidad de estar en el ranking i-esimo dada una tasa
    return List of floats"""

    base = max(0.01, min(tasa, 0.3))  # limitar valores extremos
    probs = []
    total_weight = sum([1 / (i + base * 10) for i in range(1, 11)])
    for i in range(1, 11):
        weight = 1 / (i + base * 10)
        probs.append(weight / total_weight)
    return probs

# TODO: Revisar este codigo
def estimar_probabilidades_ranking_v2(tasa, datos_modelo):
    """Dado una tasa devuelve el ranking probable
    el ranking probable se calcula mediante una regresion logistica usando datos_modelo"""
    probs = []
    if 'POSICION_RELATIVA' not in datos_modelo.columns:
        raise ValueError("Los datos no contienen la columna 'POSICION_RELATIVA'")
    if 'TASA_VENTA' not in datos_modelo.columns:
        raise ValueError("Los datos no contienen la columna 'tasa'")
    X = datos_modelo[['TASA_VENTA']].values
    y = datos_modelo['POSICION_RELATIVA'].values

    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000)
    model.fit(X, y)
    probabilidades = model.predict_proba([[tasa]])[0]
    rankings_unicos = np.sort(np.unique(y))
    probs = [(ranking, prob) for ranking, prob in zip(rankings_unicos, probabilidades)]
    probs.sort(key=lambda x: x[0])

    return probs 

def clusterizacion_jerarquica(datos, n_cluster_nivel1 =3, n_clusters_nivel2=2):
    """Cluster a 2 niveles
    Args: datos pre procesados, n clusters 1 int, n clusters 2 int"""
    # Por tasa y ranking
    scaler_n1 = StandardScaler()
    features_n1 = datos[['TASA_VENTA', 'POSICION_RELATIVA']]
    features_n1_scaled = scaler_n1.fit_transform(features_n1)

    kmeans_nivel1 = KMeans(
        n_clusters=n_cluster_nivel1,
        random_state=42,
        init='k-means++',
        n_init='auto'
    )
    datos['cluster_nivel1'] = kmeans_nivel1.fit_predict(features_n1_scaled)
    cluster_n2_labels = np.zeros(len(datos), dtype=int)*-1
    for cluster_id in range(n_cluster_nivel1):
        mask = (datos['cluster_nivel1'] == cluster_id)
        cluster_data = features_n1_scaled[mask]
        if len(cluster_data) > n_clusters_nivel2:
            kmeans_nivel2 = KMeans(
                n_clusters=n_clusters_nivel2,
                random_state=42,
                n_init=1
            )
            datos.loc[mask, 'cluster_nivel2'] = kmeans_nivel2.fit_predict(cluster_data)
        else:
            datos.loc[mask, 'cluster_nivel2'] = 0

    return datos

# Esta funcion sera utilizada solo en las presentaciones o para probar el archivo
# No es importante
def vis_clus(datos, nivel=1, sample_size=2000, random_state=42):
    """Visualizacion"""
    if len(datos) > sample_size:
        if nivel==1:
            muestra=datos.groupby('cluster_nivel1', group_keys=False).apply(lambda x : x.sample(min(len(x), max(1, int(sample_size * len(x)/ len(datos)))),
                                                                                                    random_state=random_state))
        else:
            muestra=datos.groupby('cluster_nivel2', group_keys=False).apply(lambda x: x.sample(min(len(x), max(1, int(sample_size * len(x)/len(datos)))),
                                                                                                   random_state=random_state))
    else:
        muestra = datos

    print(f"Visualizando {len(muestra)} de {len(datos)} registros")

    plt.figure(figsize=(12, 8))
    if nivel == 1:
        sns.scatterplot(data=datos, x='TASA_VENTA', y='POSICION_RELATIVA',
                        hue='cluster_nivel1', palette='viridis', s=100)
        plt.title('Clusterizacion por tasa y ranking')
    else:
        sns.scatterplot(data=datos, x='POSICION_RELATIVA', y='ACEPTADA', hue='cluster_nivel2', palette='tab10', s=100)
        plt.title('Subclusterizacion por Ranking y Aceptacion (Nivel 2)')
        plt.yticks([0,1])
    
    plt.xlabel('Tasa' if nivel==1 else 'Ranking')
    plt.ylabel('Ranking' if nivel==1 else 'Aceptacion')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(title=f'Cluster Nivel {nivel}')
    plt.tight_layout()
    plt.savefig(f'clusters_nivel_{nivel}.png')
    plt.show()

# lo mismo
def plot_clusters_3d(datos, cluster_col='cluster_nivel2',
                     features=['POSICION_RELATIVA', 'ACEPTADA', 'TASA_VENTA']):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    
    scatter = ax.scatter(
        datos[features[0]],
        datos[features[1]],
        datos[features[2]],
        c=datos[cluster_col],
        cmap='tab10',
        s=50,
        alpha=0.6
    )

    ax.set_xlabel(features[0])
    ax.set_ylabel(features[1])
    ax.set_zlabel(features[2])
    ax.set_title(f'Clusters en 3D: {cluster_col}')

    plt.colorbar(scatter)
    plt.show()

# Llamar a la función
# TODO: Corregir estas ideas con base en las ideas de N. B.
def ajustar_probs_por_perfil(probs, perfil):
    """Hace un ajuste a un vector de probabilidades considerando un factor de ajuste """
    # Ejemplo simple: si riesgo es alto, baja un poco prob ranking 1, si bajo la sube un poco
    factor = {"bajo": 1.1, "medio": 1.0, "alto": 0.9}
    ajuste = factor.get(perfil["riesgo"], 1.0)
    probs_ajust = [p * ajuste for p in probs]
    total = sum(probs_ajust)
    probs_ajust = [p / total for p in probs_ajust]
    return probs_ajust

# Simula un perfil de cliente como diccionario
## claramente esto se modifica y necesita ser parcheado
## Le pasamos los tipos de cliente y el nivel de riesgo
## Aca no debiesemos clusterizar los clientes?
def generar_perfil_cliente(tipos_cliente, niveles_riesgo):
    """pasamos tipos de clientes, niveles de riesgo
    retornamos un diccionario de key tipo y value riesgo"""
    tipo = random.choice(tipos_cliente)
    riesgo = random.choice(niveles_riesgo)
    return {"tipo": tipo, "riesgo": riesgo}

###TODO: Borrar testeo
#print('uniendo bases')
#datos = unir_cotizaciones(
#   bbdd1 = 'COTIZACIONES.xlsx',
#    bbdd2= 'SC_COTIZACIONES.xlsx',
#    base_path='BBDD'
#)
#print('guardando weaitas como picke')
#guardar_como_picke(datos, 'BBDD/datos.pkl')

# TODO: reemplazar test por main para testear
if __name__ == "__test__":
    print('clusterizando')
    datos = cargar_desde_pickle(os.path.join('BBDD')+"/datos.pkl")
    datos_clusterizados = clusterizacion_jerarquica(
        datos,
        n_cluster_nivel1=4,
        n_clusters_nivel2=2
    )

    print('visualizando')
    #vis_clus(datos_clusterizados, nivel=1, sample_size=2000, random_state=42)
    #vis_clus(datos_clusterizados, nivel=2, sample_size=2000, random_state=42)
    datos_muestra = datos_clusterizados.sample(n=500, random_state=42)
    plot_clusters_3d(datos_muestra)

    print('pasando a csv')
    datos_clusterizados.to_csv("BBDD/cluster.csv", index=False)

    print('guardando como pickle')
    # TODO: Corregir esto
    #guardar_como_picke((datos_clusterizados, modelo_n1, modelo_n2), "BBDD/modelos_cluster.pkl")

    print('Success')