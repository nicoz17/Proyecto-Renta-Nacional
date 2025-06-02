import numpy as np
import pandas as pd
import joblib
import os
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.mixture import BayesianGaussianMixture
from sklearn.pipeline import Pipeline
from functions import cargar_desde_pickle

def aprender_distribucion(df, features_numericas, features_categoricas, model_path):
    df = df[features_numericas + features_categoricas].copy()
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), features_numericas),
            ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), features_categoricas)
        ],
        remainder = 'drop'
    )
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('pca', PCA(n_components=0.95, random_state=42)),
        ('gmm', BayesianGaussianMixture(
            n_components=min(50, len(df)//200),
            covariance_type='diag',
            max_iter=500,
            random_state=42,
            verbose=1
        ))
    ])

    pipeline.fit(df)

    modelo = {
        'pipeline':pipeline,
        'features_numericas': features_numericas,
        'features_categoricas': features_categoricas
    }
    joblib.dump(modelo, model_path)
    return modelo

def samplear_distribucion(modelo, n_muestras=int):
    if isinstance(modelo, str):
        modelo = joblib.load(modelo)
    
    pipeline = modelo['pipeline']

    samplear_embeddings, _ = pipeline.named_steps['gmm'].sample(n_muestras)

    pca = pipeline.named_steps['pca']
    sampled_pca = pca.inverse_transform(samplear_embeddings)

    preprocessor = pipeline.named_steps['preprocessor']
    df_sampled = pd.DataFrame(
        sampled_pca,
        columns = preprocessor.get_feature_names_out()
    )

    scaler = preprocessor.named_transformers_['num']
    num_feature_names = [f"num__{col}" for col in modelo['features_numericas']]

    if all(col in df_sampled.columns for col in num_feature_names):
        df_sampled[num_feature_names] = scaler.inverse_transform(df_sampled[num_feature_names])
        rename_dict = {f"num__{col}": col for col in modelo['features_numericas']}
        df_sampled.rename(columns=rename_dict, inplace=True)
    else:
        print("Advertencia")
    
    ohe = preprocessor.named_transformers_['cat']

    for orig_col in modelo['features_categoricas']:
        prefix = f"cat__{orig_col}_"
        ohe_cols = [ c for c in df_sampled.columns if c.startswith(prefix)]
        if ohe_cols:
            df_sampled[orig_col] = df_sampled[ohe_cols].idxmax(axis=1).str.replace(prefix, "")
            df_sampled.drop(columns=ohe_cols, inplace=True)
    
    column_order = modelo['features_numericas'] + modelo['features_categoricas']
    available_cols = [col for col in column_order if col in df_sampled.columns]

    return df_sampled[available_cols]

# TODO: dejar como test
if __name__ == "__test__":
    # 1. Cargar datos
    print("Cargando datos...")
    ruta_pickle = os.path.join("BBDD") + "/datos.pkl" 
    df = cargar_desde_pickle(ruta_pickle)
    
    print("\nPrimeras filas del dataset:")
    print(df.head())
    
    print("\nResumen de columnas:")
    print(f"Total filas: {len(df)}")
    print(f"Columnas: {list(df.columns)}")
    print("\nTipos de datos:")
    print(df.dtypes)
    
    print("\nSeleccionando features...")
    # TODO: Revisar
    features_numericas = ['TASA_VENTA', 'MESES_GARANTIZADOS', 'RENTA', 'VAN']  # EJEMPLO
    features_categoricas = ['INVALIDA']  # EJEMPLO
    
    for col in features_numericas + features_categoricas:
        if col not in df.columns:
            print(f"¡Advertencia! Columna '{col}' no encontrada en el dataset")
    
    print("\nEntrenando modelo de distribución...")
    modelo_path = "modelo_distribucion.pkl"
    
    if os.path.exists(modelo_path):
        print("Cargando modelo existente...")
        modelo = joblib.load(modelo_path)
    else:
        pass
        print("Entrenando nuevo modelo...")
        modelo = aprender_distribucion(
            df=df,
            features_numericas=features_numericas,
            features_categoricas=features_categoricas,
            model_path=modelo_path
        )
        print("¡Modelo entrenado y guardado!")
    
    print("\nGenerando muestras...")
    muestras = samplear_distribucion(modelo, n_muestras=1000)
    
    print("\nMuestras generadas:")
    print(muestras.head())
    
    print("\nValidación básica:")
    print("Distribución variables numéricas (original vs muestra):")
    
    for col in features_numericas:
        print(f"\n{col}:")
        print(f"  Original: media={df[col].mean():.2f}, std={df[col].std():.2f}")
        print(f"  Muestra : media={muestras[col].mean():.2f}, std={muestras[col].std():.2f}")
    
    print("\nDistribución variables categóricas (original vs muestra):")
    for col in features_categoricas:
        print(f"\n{col}:")
        orig_counts = df[col].value_counts(normalize=True).head(5)
        muest_counts = muestras[col].value_counts(normalize=True).head(5)
        
        print("  Top 5 categorías original:")
        print(orig_counts)
        print("\n  Top 5 categorías muestra:")
        print(muest_counts)
    
    muestras_path = "muestras_generadas.csv"
    muestras.to_csv(muestras_path, index=False)
    print(f"\nMuestras guardadas en: {muestras_path}")
    
    print("\n¡Proceso completado!")

