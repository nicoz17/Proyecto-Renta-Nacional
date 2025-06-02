Cris 30 abril

En el cris_pipeline.ipynb deje una implementacion de una regresion logistica simple y un XGBoost. Ambos los implemente con DeepSeek y estan basados en el merge de bases de datos que hizo N. Zapata. La ultima celda de este modelo tiene una busqueda de parametros para encontrar sus mejores parametros. Tambien modifique ligeramente el .gitignore y el readme viejo. (trivial).

Repeti el codigo del random forest pero de manera que sea recicable. Para experimentar aumente la profundidad de 20 a 30 y mejoro casi nada, asi que quizas el random forest quede en 77% como tope maximo.

Algunos TO DO:

No hice analisis de que variables entraban al modelo y que variables no, tengo que hacer un analisis por correlaciones o F-score para ir descartando, pero el ipynb tiene un grafico que muestra cuales son las que aportan mas a la prediccion (con xgboost).

Hoy (29 abril) llego un correo con info extra que podemos incorporar al modelo. Estaria bueno hacer otro merge/join y ver si añadiendo mas informacion al problema mejoran los resultados predictivos.
