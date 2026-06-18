import gurobipy as gp
from conjuntos_y_parametros import Conjuntos, Parametros
from pathlib import Path
import ast
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

model = gp.Model("E3")
conjuntos = Conjuntos()
parametros = Parametros(conjuntos)

'''
Variables
'''

X = model.addVars(
    conjuntos.k,
    conjuntos.i,
    conjuntos.t,
    vtype=gp.GRB.INTEGER,
    name="X"
)
'''Cantidad de chipeadoras tipo k operativas en la zona i durante el mes t.'''

Y = model.addVars(
    conjuntos.j,
    conjuntos.i,
    conjuntos.t,
    vtype=gp.GRB.CONTINUOUS,
    name="Y"
)
'''Kg de biomasa residual tipo j procesada en la zona i durante el mes t.'''

I = model.addVars(
    conjuntos.j,
    conjuntos.i,
    conjuntos.t,
    vtype=gp.GRB.CONTINUOUS,
    name="I"
)
'''Biomasa residual tipo j remanente en la zona i al final del mes t.'''

A = model.addVars(
    conjuntos.k,
    conjuntos.i,
    conjuntos.t,
    conjuntos.f,
    vtype=gp.GRB.INTEGER,
    name="A"
)
'''Cantidad de fallas tipo f pendientes de reparación en chipeadoras tipo k, en la zona i al final del mes t.'''

Q = model.addVars(
    conjuntos.k,
    conjuntos.i,
    conjuntos.t,
    conjuntos.f,
    vtype=gp.GRB.INTEGER,
    name="Q"
)
'''Cantidad de fallas f reparadas en chipeadoras k en la zona i durante el mes t.'''

F = model.addVars(
    conjuntos.k,
    conjuntos.i,
    conjuntos.t,
    conjuntos.f,
    vtype=gp.GRB.INTEGER,
    name="F"
)
'''Cantidad de fallas f nuevas en chipeadoras k en la zona i durante el mes t.'''

Z = model.addVars(
    conjuntos.k,
    conjuntos.t,
    vtype=gp.GRB.INTEGER,
    name="Z"
)
'''Cantidad de chipeadoras tipo k compradas en el mes t.'''

H = model.addVars(
    conjuntos.i,
    conjuntos.t,
    vtype=gp.GRB.INTEGER,
    name="H"
)
'''Trabajadores contratados para la zona i durante el mes t.'''

D = model.addVars(
    conjuntos.i,
    conjuntos.t,
    vtype=gp.GRB.INTEGER,
    name="D"
)
'''Trabajadores desvinculados en la zona i durante el mes t.'''

W = model.addVars(
    conjuntos.i,
    conjuntos.t,
    vtype=gp.GRB.INTEGER,
    name="W"
)
'''Trabajadores disponibles en zona i en el mes t.'''

'''
Activación de restricciones:
    A continuación, dejaré unas variables binarias para activar o desactivar cada una de las restricciones del modelo.
    De esta forma, será más facil probar el modelo con diferentes combinaciones de restricciones en caso de que el modelo no sea factible o tenga problemas de convergencia.
'''

restricciones_activas: dict[int, bool] = {
    1:  True,
    2:  True,
    3:  True,
    4:  True,
    5:  True,
    6:  True,
    7:  True,
    8:  True,
    9:  True,
    10: True,
    11: True,
    12: True,
    13: True,
}


'''
Restricciones
'''

print(conjuntos.k)

R1 = model.addConstrs(
    (
        gp.quicksum(
            Y[j, i, t]

            for j in conjuntos.j
        )
        <=
        gp.quicksum(
            parametros.Cap_k[k-1]
            *
            (
                X[k, i, t]
                -
                gp.quicksum(
                    A[k, i, t, f]

                    for f in conjuntos.f
                )
            )

            for k in conjuntos.k
        )

    for i in conjuntos.i
    for t in conjuntos.t
    ),
    name="CapacidadProcesamiento"
) if restricciones_activas[1] else None
'''
La cantidad procesada en cada zona no puede superar la capacidad total de las chipeadoras efectivamente disponibles para operar en ese periodo, descontando aquellas que presentan fallas pendientes de reparación.
'''

R2 = model.addConstrs(
    (
        gp.quicksum(
            A[k, i, t, f]

            for f in conjuntos.f
        )
        <=
        X[k, i, t]

        for k in conjuntos.k
        for i in conjuntos.i
        for t in conjuntos.t
    ),
    name="RestriccionEficienciaChipeadoras"
) if restricciones_activas[2] else None
'''
La pérdida total de capacidad operativa generada por fallas no puede superar la cantidad de chipeadoras operativas disponibles.
'''

R3a = model.addConstrs(
    (
        I[j, i, 1]
        ==
        (
            parametros.w_ji[j-1][i-1]
            +
            parametros.G_jit[j-1][i-1][0]
            -
            Y[j, i, 1]
        )

        for j in conjuntos.j
        for i in conjuntos.i
    ),
    name="DinamicaResiduos_t1"
) if restricciones_activas[3] else None
'''
El residuo acumulado evoluciona en el tiempo según lo que queda del período anterior, lo que se genera y lo que se procesa.
'''

R3b = model.addConstrs(
    (
        I[j, i, t]
        ==
        (
            I[j, i, t-1]
            +
            parametros.G_jit[j-1][i-1][t-2]
            -
            Y[j, i, t]
        )

        for j in conjuntos.j
        for i in conjuntos.i
        for t in conjuntos.t if t != 1
    ),
    name="DinamicaResiduos_t2"
) if restricciones_activas[3] else None
'''
El residuo acumulado evoluciona en el tiempo según lo que queda del período anterior, lo que se genera y lo que se procesa.
'''

R4a = model.addConstrs(
    (
        Y[j, i, 1]
        <=
        (
            parametros.w_ji[j-1][i-1]
            +
            parametros.G_jit[j-1][i-1][0]
        )

        for j in conjuntos.j
        for i in conjuntos.i
    ),
    name="DisponibilidadResiduos_t1"
) if restricciones_activas[4] else None
'''
No se puede procesar más biomasa que la efectivamente disponible en cada período.
'''

R4b = model.addConstrs(
    (
        Y[j, i, t]
        <=
        (
            I[j, i, t-1]
            +
            parametros.G_jit[j-1][i-1][t-2]
        )

        for j in conjuntos.j
        for i in conjuntos.i
        for t in conjuntos.t if t != 1
    ),
    name="DisponibilidadResiduos_t2"
) if restricciones_activas[4] else None
'''
No se puede procesar más biomasa que la efectivamente disponible en cada período.
'''

R5 = model.addConstrs(
    (
        gp.quicksum(
            I[j, i, t]

            for j in conjuntos.j
        )
        <=
        parametros.P_it[i-1][t-2]

        for i in conjuntos.i
        for t in conjuntos.t
    ),
    name="CapacidadMaximaAlmacenamiento"
) if restricciones_activas[5] else None
'''
La biomasa residual acumulada no puede superar la capacidad de almacenamiento de la zona.
'''

R6a = model.addConstrs(
    (
        W[i, 1]
        ==
        (
            parametros.TT_i[i-1]
            +
            H[i, 1]
            -
            D[i, 1]
        )

        for i in conjuntos.i
    ),
    name="TrabajadoresDisponibles_t1"
) if restricciones_activas[6] else None
'''
La cantidad de trabajadores evoluciona según contrataciones y desvinculaciones dentro del horizonte de planificación.
'''

R6b = model.addConstrs(
    (
        W[i, t]
        ==
        (
            W[i, t-1]
            +
            H[i, t]
            -
            D[i, t]
        )

        for i in conjuntos.i
        for t in conjuntos.t if t != 1
    ),
    name="TrabajadoresDisponibles_t2"
) if restricciones_activas[6] else None
'''
La cantidad de trabajadores evoluciona según contrataciones y desvinculaciones dentro del horizonte de planificación.
'''

R7 = model.addConstrs(
    (
        gp.quicksum(
            parametros.delta_k[k-1]
            *
            X[k, i, t]

            for k in conjuntos.k
        )
        <=
        W[i, t]

        for i in conjuntos.i
        for t in conjuntos.t
    ),
    name="TrabajadoresMinimosRequeridos"
) if restricciones_activas[7] else None
'''
La cantidad de trabajadores disponibles en cada zona debe ser suficiente para operar las chipeadoras asignadas en cada periodo.
'''

R8a = model.addConstrs(
    (
        D[i, 1]
        <=
        (
            parametros.TT_i[i-1]
            +
            H[i, 1]
        )

        for i in conjuntos.i
    ),
    name="DespidoTrabajadores_t1"
) if restricciones_activas[8] else None
'''
No se puede despedir a más trabajadores que los disponibles en cada período.
'''

R8b = model.addConstrs(
    (
        D[i, t]
        <=
        W[i, t-1] + H[i, t]

        for i in conjuntos.i
        for t in conjuntos.t if t != 1
    ),
    name="DespidoTrabajadores_t2"
) if restricciones_activas[8] else None
'''
No se puede despedir a más trabajadores que los disponibles en cada período.
'''

R9a = model.addConstrs(
    (
        A[k, i, 1, f]
        ==
        (
            F[k, i, 1, f]
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for f in conjuntos.f
    ),
    name="DinamicaFallas_t1"
) if restricciones_activas[9] else None
'''
La cantidad de chipeadoras con fallas pendientes de reparación al final de cada período depende de las chipeadoras con fallas pendientes del periodo anterior, las chipeadoras con fallas nuevas ocurridas durante el mes y las chipeadoras arregladas.'''

R9b = model.addConstrs(
    (
        A[k, i, t, f]
        ==
        (
            A[k, i, t-1, f]
            +
            F[k, i, t, f]
            -
            Q[k, i, t, f]
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for t in conjuntos.t if t != 1
        for f in conjuntos.f
    ),
    name="DinamicaFallas_t2"
) if restricciones_activas[9] else None
'''
La cantidad de fallas pendientes de reparación al final de cada período depende de las fallas pendientes del periodo anterior, las fallas nuevas ocurridas y las reparaciones arregladas.
'''

R10a = model.addConstrs(
    (
        F[k, i, 1, f]
        >=
        (
            parametros.alpha_kf[k-1][f-1]
            *
            X[k, i, 1]
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for f in conjuntos.f
    ),
    name="FallasEsperadasPorUso_inicial_1"
) if restricciones_activas[10] else None

R10b = model.addConstrs(
    (
        F[k, i, 1, f]
        <=
        (
            parametros.alpha_kf[k-1][f-1]
            *
            X[k, i, 1]
            +
            0.9999999
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for f in conjuntos.f
    ),
    name="FallasEsperadasPorUso_inicial_2"
) if restricciones_activas[10] else None

R10c = model.addConstrs(
    (
        F[k, i, t, f]
        >=
        (
            parametros.alpha_kf[k-1][f-1]
            *
            (
                X[k, i, t]
                -
                gp.quicksum(
                    A[k, i, t-1, f_prime]

                    for f_prime in conjuntos.f
                )
            )
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for t in conjuntos.t
        for f in conjuntos.f if t != 1
    ),
    name="FallasEsperadasPorUso_general_1"
) if restricciones_activas[10] else None

R10d = model.addConstrs(
    (
        F[k, i, t, f]
        <=
        (
            parametros.alpha_kf[k-1][f-1]
            *
            (
                X[k, i, t]
                -
                gp.quicksum(
                    A[k, i, t-1, f_prime]

                    for f_prime in conjuntos.f
                )
            )
            +
            0.9999999
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for t in conjuntos.t
        for f in conjuntos.f if t != 1
    ),
    name="FallasEsperadasPorUso_general_2"
) if restricciones_activas[10] else None
'''
La cantidad de fallas nuevas consideradas debe ser al menos el número esperado de fallas, estimado a partir de la probabilidad de falla y la cantidad de chipeadoras operativas.
'''

R11a = model.addConstrs(
    (
        Q[k, i, 1, f]
        ==
        0

        for k in conjuntos.k
        for i in conjuntos.i
        for f in conjuntos.f
    ),
    name="ReparacionesFactibles_t1"
) if restricciones_activas[11] else None
'''
La cantidad de fallas reparadas en cada período no puede superar las fallas nuevas ni aquellas pendientes de reparación de períodos anteriores.
'''

R11b = model.addConstrs(
    (
        Q[k, i, t, f]
        <=
        (
            A[k, i, t-1, f]
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for t in conjuntos.t if t != 1
        for f in conjuntos.f
    ),
    name="ReparacionesFactibles_t2"
) if restricciones_activas[11] else None
'''
La cantidad de fallas reparadas en cada período no puede superar las fallas nuevas ni aquellas pendientes de reparación de períodos anteriores.
'''

R12 = model.addConstrs(
    (
        gp.quicksum(
            X[k, i, t]

            for i in conjuntos.i
        )
        <=
        (
            parametros.N_k[k-1]
            +
            gp.quicksum(
                Z[k, tau]

                for tau in conjuntos.t if tau <= t
            )
        )

        for k in conjuntos.k
        for t in conjuntos.t
    ),
    name="DisponibilidadChipeadoras"
) if restricciones_activas[12] else None
'''
La cantidad de chipeadoras operativas de todas las zonas $i$, no puede exceder la flota total inicial más las compras acumuladas hasta el mes $t$.
'''

R13 = model.addConstrs(
    (
        gp.quicksum(
            I[j, i, 12]

            for j in conjuntos.j
        )
        <=
        parametros.L_i[i-1]

        for i in conjuntos.i
    ),
    name="ResiduosAlFinalHorizon"
) if restricciones_activas[13] else None
'''
Al final del período (12 meses), cada zona $i$ debe cumplir con un nivel máximo de residuos permitidos.
'''

'''
Función objetivo
'''

model.setObjective(
      gp.quicksum(parametros.CO_kt[k-1][t-1] * X[k, i, t]      for k in conjuntos.k for t in conjuntos.t for i in conjuntos.i                                          )
    + gp.quicksum(parametros.CT_it[i-1][t-1] * Y[j, i, t]                           for t in conjuntos.t for i in conjuntos.i for j in conjuntos.j                     )
    + gp.quicksum(parametros.CR_kf[k-1][f-1]              * Q[k, i, t, f]   for k in conjuntos.k for t in conjuntos.t for i in conjuntos.i                      for f in conjuntos.f)
    + gp.quicksum(parametros.h_ji[j-1][i-1]               * I[j, i, t]                           for t in conjuntos.t for i in conjuntos.i for j in conjuntos.j                     )
    + gp.quicksum(parametros.PC_k[k-1]                  * Z[k, t]         for k in conjuntos.k for t in conjuntos.t                                                               )
    + gp.quicksum(parametros.CC_it[i-1][t-1] * H[i, t]                              for t in conjuntos.t for i in conjuntos.i                                          )
    + gp.quicksum(parametros.CF_it[i-1][t-1] * D[i, t]                              for t in conjuntos.t for i in conjuntos.i                                          )
    + gp.quicksum(parametros.ST_it[i-1][t-1] * W[i, t]                              for t in conjuntos.t for i in conjuntos.i                                          ),
    sense=gp.GRB.MINIMIZE
)

'''
Configuración de parámetros de optimización
'''

model.Params.TimeLimit = 600
model.Params.MIPGap = 0.01
model.Params.LogToConsole = 1

'''
Ejecución de optimización
'''

model.optimize()


'''
Guardado de resultados
'''

output_path = Path(__file__).with_name("resultados_variables.txt")

if model.SolCount > 0:
    with output_path.open("w", encoding="utf-8") as f:
        for nombre, vars_dict in [
            ("X", X),
            ("Y", Y),
            ("I", I),
            ("A", A),
            ("Q", Q),
            ("F", F),
            ("Z", Z),
            ("H", H),
            ("D", D),
            ("W", W),
        ]:
            f.write(f"{nombre}\n")
            for key, var in vars_dict.items():
                f.write(f"{key}: {var.X}\n")
            f.write("\n")
else:
    with output_path.open("w", encoding="utf-8") as f:
        f.write("No feasible solution found.\n")


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


def generar_graficos_desde_txt(ruta_txt: Path):
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

    carpeta = Path(__file__).with_name("graficos_resultados")
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
    # 2. Trabajadores desvinculados por región
    # ==========================

    desvinculados_zona = []

    for i in conjuntos.i:
        total_zona = sum(
            valor
            for (ii, t), valor in resultados["D"].items()
            if ii == i
        )
        desvinculados_zona.append(total_zona)

    plt.figure(figsize=(8, 4.8))
    plt.bar([zonas[i] for i in conjuntos.i], desvinculados_zona)
    plt.title("Trabajadores desvinculados totales por región")
    plt.xlabel("Región")
    plt.ylabel("Trabajadores desvinculados")
    plt.xticks(rotation=20, ha="right")
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


if model.SolCount > 0:
    generar_graficos_desde_txt(output_path)