import random
from collections import Counter
from functions import estimar_probabilidades_ranking_v2
from functions import generar_perfil_cliente, estimar_probabilidades_ranking, ajustar_probs_por_perfil
from clientes_dist import samplear_distribucion
from parametros import dias_del_mes, ranking_acumulado_mes, ventas_acumuladas, clientes_totales, rankings_totales
from modelo_ces import cargar_datos, predict_auto_arima
from functions import cargar_desde_pickle

# PARAMETROS
tipos_cliente = ["tipo 1", "tipo 2", "tipo 3", "tipo 4"]
niveles_riesgo = ["bajo", "medio", "alto"]
## Cargar funciones previas
# Serie de tiempo
# Generacion del excel
base_path = "BBDD"
serie = cargar_datos(base_path)
forecast = predict_auto_arima(serie, n_steps=14)

for dia in dias_del_mes:
    print(f"\n🗓️ Día {dia}")

    
    # TODO: reemplazar por el ARIMA 
    # TODO: revisar el numero de steps
    ## Hacer una clusterizacion de los clientes
    # En vola un cliente se puede modelar como una clase con id, tipo y nivel de riesgo

    forecast = predict_auto_arima(serie, n_steps=dia)
    n_clientes = int(forecast.iloc[0])
    #n_clientes = random.randint(5, 6)
    #print(f"📌 Clientes esperados hoy: {n_clientes}\n")
    
    print(f'n_clientes {n_clientes} dia {dia}')
    # TODO: Hacer sampling
    perfiles_clientes = samplear_distribucion('modelo_distribucion.pkl', n_clientes)
    print(perfiles_clientes)
    clientes_totales += n_clientes

    # Pedir tasa
    while True:
        try:
            tasa = float(input("✍️ Ingresa la tasa para el día (ej. 0.12): "))
            break
        except ValueError:
            print("⚠️ Por favor, ingresa un número válido.")

    while True:

        # TODO: Incluir sugerencia de estimar_probabilidades_ranking_v2
        probs_base = estimar_probabilidades_ranking_v2(tasa, cargar_desde_pickle(base_path+"/datos.pkl"))
        print('Sugerencia')
        # Hasta aca funciona
        # TODO: Incluir input de ajuste manual si es necesario

        # Mostrar probabilidad para cada perfil:
        # TODO: Aun no definimos los perfiles
        for idx, perfil in enumerate(perfiles_clientes, start=1):
            probs_ajust = ajustar_probs_por_perfil(probs_base, perfil)
            print(f"La probabilidad de quedar en cada ranking para el perfil Cliente {idx}: {perfil['tipo']}, riesgo {perfil['riesgo']} es:")
            for i, p in enumerate(probs_ajust, start=1):
                print(f"  Ranking {i}: {p*100:.2f}%")
            print()

        print("❓ ¿Qué quieres hacer ahora?")
        print("1 → Cambiar la tasa y volver a calcular")
        print("2 → Mantener la tasa y usar ponderación para rankings estimados")
        print("3 → Mantener la tasa y asignar rankings manualmente")

        while True:
            opcion = input("Selecciona una opción (1/2/3): ")
            if opcion in {'1', '2', '3'}:
                break
            else:
                print("⚠️ Opción no válida. Elige 1, 2 o 3.")

        if opcion == '1':
            try:
                tasa = float(input("✍️ Ingresa la nueva tasa: "))
            except ValueError:
                print("⚠️ Valor no válido. Volviendo a pedir.")
            continue
        else:
            break

    rankings_dia = []
    for idx, perfil in enumerate(perfiles_clientes, start=1):
        tipo = perfil["tipo"]
        riesgo = perfil["riesgo"]
        print(f"\n👤 Cliente {idx} — Perfil: {tipo}, riesgo {riesgo}")

        if opcion == '2':
            probs_ajust = ajustar_probs_por_perfil(probs_base, perfil)
            ranking = random.choices(range(1, 11), weights=probs_ajust, k=1)[0]
            print(f"🔮 Ranking ponderado estimado: {ranking}")
        else:
            while True:
                try:
                    ranking = int(input("✍️ Ingresa el ranking manual (1-10): "))
                    if 1 <= ranking <= 10:
                        break
                    else:
                        print("⚠️ Ranking fuera de rango.")
                except ValueError:
                    print("⚠️ Debe ser un número entero.")
        rankings_dia.append(ranking)

    rankings_totales.extend(rankings_dia)

    # Simulación simple venta diaria
    #TODO: Implementar esto bien
    venta_dia = round(sum([random.uniform(200, 500) for _ in rankings_dia]), 2)
    ventas_acumuladas.append(venta_dia)
    ranking_promedio_dia = round(sum(rankings_dia) / len(rankings_dia), 2)
    ranking_acumulado_mes.append(ranking_promedio_dia)

    print(f"\n📊 Resumen del día {dia}:")
    print(f"   → Tasa usada: {tasa}")
    print(f"   → Rankings del día: {rankings_dia}")
    print(f"   → Ranking promedio del día: {ranking_promedio_dia}")
    print(f"   → Venta estimada: ${venta_dia}")

    promedio_mes_actual = round(sum(ranking_acumulado_mes) / len(ranking_acumulado_mes), 2)
    ventas_totales = round(sum(ventas_acumuladas), 2)

    print(f"\n📘 Resumen acumulado hasta el día {dia}:")
    print(f"   → Ranking promedio mensual: {promedio_mes_actual}")

    contador_rankings = Counter(rankings_totales)
    total_rankings = len(rankings_totales)
    for i in range(1, 11):
        porcentaje = (contador_rankings[i] / total_rankings) * 100 if total_rankings > 0 else 0
        print(f"   %Ranking {i} = {porcentaje:.2f}%")

    print(f"   → Total clientes atendidos: {clientes_totales}")
    print(f"   → Ventas acumuladas estimadas: ${ventas_totales}")

    seguir = input("\n🔄 ¿Quieres continuar al siguiente día? (s para sí, cualquier otra tecla para salir): ").lower()
    if seguir != 's':
        break

print("\n📝 Simulación finalizada. Gracias por usar el sistema.")
