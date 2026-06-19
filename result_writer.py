import ast
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def leer_resultados_txt(ruta_txt: Path) -> dict:
    resultados = {}
    variable_actual = None

    with ruta_txt.open("r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()

            if not linea:
                continue

            if linea in ["X", "Y", "I", "A", "Q", "F", "Z", "H", "D", "W"]:
                variable_actual = linea
                resultados[variable_actual] = {}
                continue

            if variable_actual is not None and ":" in linea:
                key_txt, valor_txt = linea.split(":", 1)
                key = ast.literal_eval(key_txt.strip())
                valor = float(valor_txt.strip())
                resultados[variable_actual][key] = valor

    return resultados


def generar_graficos_desde_txt(conjuntos, ruta_txt: Path):
    resultados = leer_resultados_txt(ruta_txt)

    meses = {
        1: "mayo", 2: "junio", 3: "julio", 4: "agosto",
        5: "septiembre", 6: "octubre", 7: "noviembre", 8: "diciembre",
        9: "enero", 10: "febrero", 11: "marzo", 12: "abril"
    }

    zonas = {
        1: "Región del Maule",
        2: "Región del Biobío",
        3: "Región de la Araucanía"
    }

    carpeta = ruta_txt.parent / "graficos"
    carpeta.mkdir(exist_ok=True)

    # ==========================
    # 1. Biomasa procesada por mes
    # ==========================

    biomasa_mes = []

    for t in conjuntos.t:
        total_mes = sum(
            valor
            for (j, i, tt), valor in resultados["Y"].items()
            if tt == t
        )
        biomasa_mes.append(total_mes / 1_000_000)

    plt.figure(figsize=(9, 4.8))
    plt.plot([meses[t] for t in conjuntos.t], biomasa_mes, marker="o")
    plt.title("Biomasa residual procesada durante el horizonte de planificación")
    plt.xlabel("Mes")
    plt.ylabel("Millones de kg procesados")
    plt.xticks(rotation=35, ha="right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(carpeta / "biomasa-procesada.png", dpi=300)
    plt.close()

    # ==========================
    # 2. Trabajadores contratados y desvinculados por región
    # ==========================

    contratados_zona = []
    desvinculados_zona = []

    for i in conjuntos.i:
        total_cont = sum(
            valor
            for (ii, t), valor in resultados["H"].items()
            if ii == i
        )
        total_desv = sum(
            valor
            for (ii, t), valor in resultados["D"].items()
            if ii == i
        )
        contratados_zona.append(total_cont)
        desvinculados_zona.append(total_desv)

    plt.figure(figsize=(8, 4.8))
    x = np.arange(len(conjuntos.i))
    width = 0.35
    plt.bar(x - width/2, contratados_zona, width, label="Contratados", color="steelblue")
    plt.bar(x + width/2, desvinculados_zona, width, label="Desvinculados", color="indianred")
    plt.title("Trabajadores contratados y desvinculados totales por región")
    plt.xlabel("Región")
    plt.ylabel("Trabajadores")
    plt.xticks(ticks=x, labels=[zonas[i] for i in conjuntos.i], rotation=20, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(carpeta / "desvinculados.png", dpi=300)
    plt.close()


    # ==========================
    # 3. Asignación mensual de chipeadoras por zona (mapa de calor)
    # ==========================

    # Build a matrix: rows = zonas, columns = meses
    heatmap_data = []
    for i in conjuntos.i:
        fila = []
        for t in conjuntos.t:
            total_zona_mes = sum(
                valor
                for (k, ii, tt), valor in resultados["X"].items()
                if ii == i and tt == t
            )
            fila.append(total_zona_mes)
        heatmap_data.append(fila)

    heatmap_array = np.array(heatmap_data)

    plt.figure(figsize=(9, 4.8))
    im = plt.imshow(heatmap_array, cmap="YlOrRd", aspect="auto")

    # Add text annotations in each cell
    for i in range(heatmap_array.shape[0]):
        for t in range(heatmap_array.shape[1]):
            plt.text(t, i, str(int(heatmap_array[i, t])),
                     ha="center", va="center",
                     color="black" if heatmap_array[i, t] < heatmap_array.max() * 0.7 else "white")

    plt.xticks(
        ticks=range(len(conjuntos.t)),
        labels=[meses[t] for t in conjuntos.t],
        rotation=35, ha="right"
    )
    plt.yticks(
        ticks=range(len(conjuntos.i)),
        labels=[zonas[i] for i in conjuntos.i]
    )
    plt.title("Asignación mensual de chipeadoras por zona (mapa de calor)")
    plt.xlabel("Mes")
    plt.ylabel("Zona")
    plt.colorbar(im, label="Cantidad de chipeadoras asignadas")
    plt.tight_layout()
    plt.savefig(carpeta / "asignacion-chipeadoras.png", dpi=300)
    plt.close()

    print("Gráficos generados correctamente en:", carpeta)


def generar_resumen(conjuntos, parametros, model, resultados: dict, ruta_txt: Path):
    meses_nombres = {
        1: "mayo", 2: "junio", 3: "julio", 4: "agosto",
        5: "septiembre", 6: "octubre", 7: "noviembre", 8: "diciembre",
        9: "enero", 10: "febrero", 11: "marzo", 12: "abril"
    }
    zonas_nombres = {1: "Maule", 2: "Biobío", 3: "Araucanía"}

    carpeta = ruta_txt
    archivo_resumen = carpeta / "resumen_resultados.txt"

    with archivo_resumen.open("w", encoding="utf-8") as f:
        print("RESUMEN DE RESULTADOS")
        f.write("RESUMEN DE RESULTADOS\n")

        print(f"\nValor óptimo de la función objetivo: {model.ObjVal:,.2f}")
        f.write(f"\nValor óptimo de la función objetivo: {model.ObjVal:,.2f}\n")

        print("Biomasa residual final (mes 12) por zona:")
        f.write("Biomasa residual final (mes 12) por zona:\n")
        for i in conjuntos.i:
            total = sum(
                valor
                for (j, ii, tt), valor in resultados["I"].items()
                if ii == i and tt == 12
            )
            line = f"   {zonas_nombres[i]:15s}: {total:>12,.0f} kg"
            print(line)
            f.write(line + "\n")

        print("Biomasa total procesada por zona (todo el año):")
        f.write("Biomasa total procesada por zona (todo el año):\n")
        for i in conjuntos.i:
            total = sum(
                valor
                for (j, ii, tt), valor in resultados["Y"].items()
                if ii == i
            )
            line = f"   {zonas_nombres[i]:15s}: {total:>12,.0f} kg"
            print(line)
            f.write(line + "\n")

        print("Trabajadores:")
        f.write("Trabajadores:\n")
        for i in conjuntos.i:
            contratados = sum(
                valor
                for (ii, tt), valor in resultados["H"].items()
                if ii == i
            )
            desvinculados = sum(
                valor
                for (ii, tt), valor in resultados["D"].items()
                if ii == i
            )
            total_mes12 = resultados["W"].get((i, 12), 0)
            line1 = f"   {zonas_nombres[i]:15s}:"
            print(line1)
            f.write(line1 + "\n")
            line2 = f"      Contratados totales  : {contratados:>5.0f}"
            print(line2)
            f.write(line2 + "\n")
            line3 = f"      Desvinculados totales: {desvinculados:>5.0f}"
            print(line3)
            f.write(line3 + "\n")
            line4 = f"      Disponibles mes 12   : {total_mes12:>5.0f}"
            print(line4)
            f.write(line4 + "\n")

        print("Chipeadoras compradas:")
        f.write("Chipeadoras compradas:\n")
        for k in conjuntos.k:
            total = sum(
                valor
                for (kk, tt), valor in resultados["Z"].items()
                if kk == k
            )
            if total > 0:
                line = f"   Tipo {k}: {total:>3.0f} unidades compradas en total"
                print(line)
                f.write(line + "\n")

        total_compradas = sum(
            valor for valor in resultados["Z"].values()
        )
        line = f"   {'Total':15s}: {total_compradas:>3.0f} unidades"
        print(line)
        f.write(line + "\n")

        print("Flota total de chipeadoras al mes 12:")
        f.write("Flota total de chipeadoras al mes 12:\n")
        for k in conjuntos.k:
            total = parametros.N_k[k-1] + sum(
                valor
                for (kk, tt), valor in resultados["Z"].items()
                if kk == k and tt <= 12
            )
            line = f"   Tipo {k}: {total:>3.0f} unidades"
            print(line)
            f.write(line + "\n")

        print("Asignación promedio de chipeadoras por zona:")
        f.write("Asignación promedio de chipeadoras por zona:\n")
        for i in conjuntos.i:
            total_anual = sum(
                valor
                for (k, ii, tt), valor in resultados["X"].items()
                if ii == i
            )
            promedio = total_anual / 12
            line = f"   {zonas_nombres[i]:15s}: {promedio:>5.1f} chipeadoras promedio/mes"
            print(line)
            f.write(line + "\n")

        print("\n" + "=" * 70)
        f.write("\n" + "=" * 70 + "\n")

    print(f"\nResumen guardado en: {archivo_resumen}")