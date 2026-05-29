import gurobipy as gp
from conjuntos_y_parametros import Conjuntos, Parametros

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
            -
            Q[k, i, 1, f]
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for f in conjuntos.f
    ),
    name="DinamicaFallas_t1"
) if restricciones_activas[9] else None
'''
La cantidad de fallas pendientes de reparación al final de cada período depende de las fallas pendientes del periodo anterior, las fallas nuevas ocurridas y las reparaciones arregladas.
'''

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
        F[k, i, t, f]
        >=
        (
            parametros.alpha_kf[k-1][f-1]
            *
            X[k, i, t]
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for t in conjuntos.t
        for f in conjuntos.f
    ),
    name="FallasEsperadasPorUso"
) if restricciones_activas[10] else None

R10b = model.addConstrs(
    (
        F[k, i, t, f]
        <=
        (
            parametros.alpha_kf[k-1][f-1]
            *
            X[k, i, t]
            +
            1
        )

        for k in conjuntos.k
        for i in conjuntos.i
        for t in conjuntos.t
        for f in conjuntos.f
    ),
    name="FallasEsperadasPorUso"
) if restricciones_activas[10] else None
'''
La cantidad de fallas nuevas consideradas debe ser al menos el número esperado de fallas, estimado a partir de la probabilidad de falla y la cantidad de chipeadoras operativas.
'''

R11a = model.addConstrs(
    (
        Q[k, i, 1, f]
        <=
        F[k, i, 1, f]

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
            +
            F[k, i, t, f]
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
