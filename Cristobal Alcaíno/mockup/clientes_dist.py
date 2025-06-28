import numpy as np
import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.mixture import BayesianGaussianMixture
from sklearn.pipeline import Pipeline
from scipy.stats import ks_2samp, chi2_contingency, wasserstein_distance
import warnings
warnings.filterwarnings('ignore')

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

def validar_distribuciones(df_original, df_muestra, features_numericas, features_categoricas, output_dir='validacion_plots'):
    """Valida las distribuciones"""
    import os
    os.makedirs(output_dir, exist_ok = True)

    resultados_numericos = {}

    n_num = len(features_numericas)
    if n_num > 0:
        fig, axes = plt.subplots(n_num, 3, figsize=(15, 5*n_num))
        if n_num ==1:
            axes = axes.reshape(-1,1)
        
        for i, col in enumerate(features_numericas):
            if col not in df_original.columns or col not in df_muestra.columns:
                print(f"{col} no encontrada")
                continue
            orig_data = df_original[col].dropna()
            muestra_data = df_muestra[col].dropna()

            ks_stat, ks_pvalue = ks_2samp(orig_data, muestra_data)
            wasserstein_dist = wasserstein_distance(orig_data, muestra_data)

            diff_mean = abs(orig_data.mean() - muestra_data.mean())
            diff_std = abs(orig_data.std() - muestra_data.std())
            diff_skew = abs(orig_data.skew() - muestra_data.skew())

            resultados_numericos[col] = {
                'ks_statistic': ks_stat,
                'ks_pvalue' : ks_pvalue,
                'wasserstein_distance': wasserstein_distance,
                'diff_mean' : diff_mean,
                'diff_std' : diff_std,
                'diff_skewness': diff_skew
            }
            print(f"\n{col.upper()}:")
            print(f"  KS Test: statistic={ks_stat:.4f}, p-value={ks_pvalue:.4f}")
            print(f"  {'✓ Distribuciones similares' if ks_pvalue > 0.05 else '✗ Distribuciones diferentes'}")
            print(f"  Wasserstein Distance: {wasserstein_dist:.4f}")
            print(f"  Diff Media: {diff_mean:.4f}, Diff Std: {diff_std:.4f}")
            
            # GRÁFICOS
            # 1. Histogramas superpuestos
            axes[i, 0].hist(orig_data, alpha=0.7, label='Original', bins=30, density=True)
            axes[i, 0].hist(muestra_data, alpha=0.7, label='Sintética', bins=30, density=True)
            axes[i, 0].set_title(f'{col} - Histogramas')
            axes[i, 0].legend()
            axes[i, 0].grid(True, alpha=0.3)
            
            # 2. Q-Q Plot
            from scipy.stats import probplot
            sorted_orig = np.sort(orig_data)
            sorted_muestra = np.sort(muestra_data)
            
            # Interpolar para mismo tamaño
            if len(sorted_orig) != len(sorted_muestra):
                min_len = min(len(sorted_orig), len(sorted_muestra))
                orig_interp = np.interp(np.linspace(0, 1, min_len), 
                                      np.linspace(0, 1, len(sorted_orig)), sorted_orig)
                muestra_interp = np.interp(np.linspace(0, 1, min_len), 
                                         np.linspace(0, 1, len(sorted_muestra)), sorted_muestra)
            else:
                orig_interp, muestra_interp = sorted_orig, sorted_muestra
            
            axes[i, 1].scatter(orig_interp, muestra_interp, alpha=0.6, s=10)
            min_val = min(orig_interp.min(), muestra_interp.min())
            max_val = max(orig_interp.max(), muestra_interp.max())
            axes[i, 1].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)
            axes[i, 1].set_xlabel('Original')
            axes[i, 1].set_ylabel('Sintética')
            axes[i, 1].set_title(f'{col} - Q-Q Plot')
            axes[i, 1].grid(True, alpha=0.3)
            
            # 3. Boxplots comparativos
            data_box = [orig_data, muestra_data]
            axes[i, 2].boxplot(data_box, labels=['Original', 'Sintética'])
            axes[i, 2].set_title(f'{col} - Boxplots')
            axes[i, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/variables_numericas.png", dpi=300, bbox_inches='tight')
        plt.show()

        print("\nVARIABLES NUMÉRICAS:")
        if resultados_numericos:
            for col, results in resultados_numericos.items():
                status = "✓ PASS" if results['ks_pvalue'] > 0.05 else "✗ FAIL"
                print(f"  {col}: {status} (p-value: {results['ks_pvalue']:.4f})")
        else:
            print("  No hay variables numéricas para validar")

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
    # TODO: Definir bien features numericas
    features_numericas = ['TASA_VENTA', 'MESES_GARANTIZADOS', 'RENTA', 'VAN']  # EJEMPLO
    features_categoricas = ['INVALIDA']  # EJEMPLO
    
    for col in features_numericas + features_categoricas:
        if col not in df.columns:
            print(f"¡Advertencia! Columna '{col}' no encontrada en el dataset")
    
    print("\nEntrenando modelo de distribución...")
    modelo_path = "modelo_distribucion.pkl"
    
    if os.path.exists(modelo_path):
        # carga el pkl si es que existe
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
    
    # validacion mas sofisticada
    resultados_validacion = validar_distribuciones(df_original=df, df_muestra=muestras, features_numericas=features_numericas, features_categoricas=features_categoricas)
    muestras_path = "muestras_generadas.csv"
    muestras.to_csv(muestras_path, index=False)
    print(f"\nMuestras guardadas en: {muestras_path}")
    
    print("\n¡Proceso completado!")

