import gurobipy as gp
from conjuntos_y_parametros import Conjuntos, Parametros, ParametrosEnum
from pathlib import Path
from result_writer import leer_resultados_txt, generar_resumen, generar_graficos_desde_txt

class OptiModel:
    def __init__(self, parametro_variado: ParametrosEnum = None, escala: float = 1.0):
        self.model = gp.Model("E3")
        self.conjuntos = Conjuntos()
        self.parametros = Parametros(self.conjuntos)
        self.run_name = f"run_param_{parametro_variado.name}_escala_{escala}" if parametro_variado is not None else "run_base"
        if parametro_variado is not None:
            self.parametros.change_parameter_scale(parametro_variado, escala)
        self.definir_variables()
        self.definir_restricciones()
        self.definir_funcion_objetivo()
        self.optimizar()
        self.guardar_resultados()

    def definir_variables(self):
        self.X = self.model.addVars(
            self.conjuntos.k,
            self.conjuntos.i,
            self.conjuntos.t,
            vtype=gp.GRB.INTEGER,
            name="X"
        )
        '''Cantidad de chipeadoras tipo k operativas en la zona i durante el mes t.'''

        self.Y = self.model.addVars(
            self.conjuntos.j,
            self.conjuntos.i,
            self.conjuntos.t,
            vtype=gp.GRB.CONTINUOUS,
            name="Y"
        )
        '''Kg de biomasa residual tipo j procesada en la zona i durante el mes t.'''

        self.I = self.model.addVars(
            self.conjuntos.j,
            self.conjuntos.i,
            self.conjuntos.t,
            vtype=gp.GRB.CONTINUOUS,
            name="I"
        )
        '''Biomasa residual tipo j remanente en la zona i al final del mes t.'''

        self.A = self.model.addVars(
            self.conjuntos.k,
            self.conjuntos.i,
            self.conjuntos.t,
            self.conjuntos.f,
            vtype=gp.GRB.INTEGER,
            name="A"
        )
        '''Cantidad de fallas tipo f pendientes de reparación en chipeadoras tipo k, en la zona i al final del mes t.'''

        self.Q = self.model.addVars(
            self.conjuntos.k,
            self.conjuntos.i,
            self.conjuntos.t,
            self.conjuntos.f,
            vtype=gp.GRB.INTEGER,
            name="Q"
        )
        '''Cantidad de fallas f reparadas en chipeadoras k en la zona i durante el mes t.'''

        self.F = self.model.addVars(
            self.conjuntos.k,
            self.conjuntos.i,
            self.conjuntos.t,
            self.conjuntos.f,
            vtype=gp.GRB.INTEGER,
            name="F"
        )
        '''Cantidad de fallas f nuevas en chipeadoras k en la zona i durante el mes t.'''

        self.Z = self.model.addVars(
            self.conjuntos.k,
            self.conjuntos.t,
            vtype=gp.GRB.INTEGER,
            name="Z"
        )
        '''Cantidad de chipeadoras tipo k compradas en el mes t.'''

        self.H = self.model.addVars(
            self.conjuntos.i,
            self.conjuntos.t,
            vtype=gp.GRB.INTEGER,
            name="H"
        )
        '''Trabajadores contratados para la zona i durante el mes t.'''

        self.D = self.model.addVars(
            self.conjuntos.i,
            self.conjuntos.t,
            vtype=gp.GRB.INTEGER,
            name="D"
        )
        '''Trabajadores desvinculados en la zona i durante el mes t.'''

        self.W = self.model.addVars(
            self.conjuntos.i,
            self.conjuntos.t,
            vtype=gp.GRB.INTEGER,
            name="W"
        )
        '''Trabajadores disponibles en zona i en el mes t.'''

    def definir_restricciones(self):
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

        self.R1 = self.model.addConstrs(
            (
                gp.quicksum(
                    self.Y[j, i, t]

                    for j in self.conjuntos.j
                )
                <=
                gp.quicksum(
                    self.parametros.Cap_k[k-1]
                    *
                    (
                        self.X[k, i, t]
                        -
                        gp.quicksum(
                            self.A[k, i, t, f]

                            for f in self.conjuntos.f
                        )
                    )

                    for k in self.conjuntos.k
                )

            for i in self.conjuntos.i
            for t in self.conjuntos.t
            ),
            name="CapacidadProcesamiento"
        ) if restricciones_activas[1] else None
        '''
        La cantidad procesada en cada zona no puede superar la capacidad total de las chipeadoras efectivamente disponibles para operar en ese periodo, descontando aquellas que presentan fallas pendientes de reparación.
        '''

        self.R2 = self.model.addConstrs(
            (
                gp.quicksum(
                    self.A[k, i, t, f]

                    for f in self.conjuntos.f
                )
                <=
                self.X[k, i, t]

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for t in self.conjuntos.t
            ),
            name="RestriccionEficienciaChipeadoras"
        ) if restricciones_activas[2] else None
        '''
        La pérdida total de capacidad operativa generada por fallas no puede superar la cantidad de chipeadoras operativas disponibles.
        '''

        self.R3a = self.model.addConstrs(
            (
                self.I[j, i, 1]
                ==
                (
                    self.parametros.w_ji[j-1][i-1]
                    +
                    self.parametros.G_jit[j-1][i-1][0]
                    -
                    self.Y[j, i, 1]
                )

                for j in self.conjuntos.j
                for i in self.conjuntos.i
            ),
            name="DinamicaResiduos_t1"
        ) if restricciones_activas[3] else None
        '''
        El residuo acumulado evoluciona en el tiempo según lo que queda del período anterior, lo que se genera y lo que se procesa.
        '''

        self.R3b = self.model.addConstrs(
            (
                self.I[j, i, t]
                ==
                (
                    self.I[j, i, t-1]
                    +
                    self.parametros.G_jit[j-1][i-1][t-2]
                    -
                    self.Y[j, i, t]
                )

                for j in self.conjuntos.j
                for i in self.conjuntos.i
                for t in self.conjuntos.t if t != 1
            ),
            name="DinamicaResiduos_t2"
        ) if restricciones_activas[3] else None
        '''
        El residuo acumulado evoluciona en el tiempo según lo que queda del período anterior, lo que se genera y lo que se procesa.
        '''

        self.R4a = self.model.addConstrs(
            (
                self.Y[j, i, 1]
                <=
                (
                    self.parametros.w_ji[j-1][i-1]
                    +
                    self.parametros.G_jit[j-1][i-1][0]
                )

                for j in self.conjuntos.j
                for i in self.conjuntos.i
            ),
            name="DisponibilidadResiduos_t1"
        ) if restricciones_activas[4] else None
        '''
        No se puede procesar más biomasa que la efectivamente disponible en cada período.
        '''

        self.R4b = self.model.addConstrs(
            (
                self.Y[j, i, t]
                <=
                (
                    self.I[j, i, t-1]
                    +
                    self.parametros.G_jit[j-1][i-1][t-2]
                )

                for j in self.conjuntos.j
                for i in self.conjuntos.i
                for t in self.conjuntos.t if t != 1
            ),
            name="DisponibilidadResiduos_t2"
        ) if restricciones_activas[4] else None
        '''
        No se puede procesar más biomasa que la efectivamente disponible en cada período.
        '''

        self.R5 = self.model.addConstrs(
            (
                gp.quicksum(
                    self.I[j, i, t]

                    for j in self.conjuntos.j
                )
                <=
                self.parametros.P_it[i-1][t-2]

                for i in self.conjuntos.i
                for t in self.conjuntos.t
            ),
            name="CapacidadMaximaAlmacenamiento"
        ) if restricciones_activas[5] else None
        '''
        La biomasa residual acumulada no puede superar la capacidad de almacenamiento de la zona.
        '''

        self.R6a = self.model.addConstrs(
            (
                self.W[i, 1]
                ==
                (
                    self.parametros.TT_i[i-1]
                    +
                    self.H[i, 1]
                    -
                    self.D[i, 1]
                )

                for i in self.conjuntos.i
            ),
            name="TrabajadoresDisponibles_t1"
        ) if restricciones_activas[6] else None
        '''
        La cantidad de trabajadores evoluciona según contrataciones y desvinculaciones dentro del horizonte de planificación.
        '''

        self.R6b = self.model.addConstrs(
            (
                self.W[i, t]
                ==
                (
                    self.W[i, t-1]
                    +
                    self.H[i, t]
                    -
                    self.D[i, t]
                )

                for i in self.conjuntos.i
                for t in self.conjuntos.t if t != 1
            ),
            name="TrabajadoresDisponibles_t2"
        ) if restricciones_activas[6] else None
        '''
        La cantidad de trabajadores evoluciona según contrataciones y desvinculaciones dentro del horizonte de planificación.
        '''

        self.R7 = self.model.addConstrs(
            (
                gp.quicksum(
                    self.parametros.delta_k[k-1]
                    *
                    self.X[k, i, t]

                    for k in self.conjuntos.k
                )
                <=
                self.W[i, t]

                for i in self.conjuntos.i
                for t in self.conjuntos.t
            ),
            name="TrabajadoresMinimosRequeridos"
        ) if restricciones_activas[7] else None
        '''
        La cantidad de trabajadores disponibles en cada zona debe ser suficiente para operar las chipeadoras asignadas en cada periodo.
        '''

        self.R8a = self.model.addConstrs(
            (
                self.D[i, 1]
                <=
                (
                    self.parametros.TT_i[i-1]
                    +
                    self.H[i, 1]
                )

                for i in self.conjuntos.i
            ),
            name="DespidoTrabajadores_t1"
        ) if restricciones_activas[8] else None
        '''
        No se puede despedir a más trabajadores que los disponibles en cada período.
        '''

        self.R8b = self.model.addConstrs(
            (
                self.D[i, t]
                <=
                self.W[i, t-1] + self.H[i, t]

                for i in self.conjuntos.i
                for t in self.conjuntos.t if t != 1
            ),
            name="DespidoTrabajadores_t2"
        ) if restricciones_activas[8] else None
        '''
        No se puede despedir a más trabajadores que los disponibles en cada período.
        '''

        self.R9a = self.model.addConstrs(
            (
                self.A[k, i, 1, f]
                ==
                (
                    self.F[k, i, 1, f]
                    -
                    self.Q[k, i, 1, f]
                )

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for f in self.conjuntos.f
            ),
            name="DinamicaFallas_t1"
        ) if restricciones_activas[9] else None
        '''
        La cantidad de chipeadoras con fallas pendientes de reparación al final de cada período depende de las chipeadoras con fallas pendientes del periodo anterior, las chipeadoras con fallas nuevas ocurridas durante el mes y las chipeadoras arregladas.'''

        self.R9b = self.model.addConstrs(
            (
                self.A[k, i, t, f]
                ==
                (
                    self.A[k, i, t-1, f]
                    +
                    self.F[k, i, t, f]
                    -
                    self.Q[k, i, t, f]
                )

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for t in self.conjuntos.t if t != 1
                for f in self.conjuntos.f
            ),
            name="DinamicaFallas_t2"
        ) if restricciones_activas[9] else None
        '''
        La cantidad de fallas pendientes de reparación al final de cada período depende de las fallas pendientes del periodo anterior, las fallas nuevas ocurridas y las reparaciones arregladas.
        '''

        self.R10a = self.model.addConstrs(
            (
                self.F[k, i, 1, f]
                >=
                (
                    self.parametros.alpha_kf[k-1][f-1]
                    *
                    self.X[k, i, 1]
                )

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for f in self.conjuntos.f
            ),
            name="FallasEsperadasPorUso_inicial_1"
        ) if restricciones_activas[10] else None

        self.R10b = self.model.addConstrs(
            (
                self.F[k, i, 1, f]
                <=
                (
                    self.parametros.alpha_kf[k-1][f-1]
                    *
                    self.X[k, i, 1]
                    +
                    0.9999999
                )

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for f in self.conjuntos.f
            ),
            name="FallasEsperadasPorUso_inicial_2"
        ) if restricciones_activas[10] else None

        self.R10c = self.model.addConstrs(
            (
                self.F[k, i, t, f]
                >=
                (
                    self.parametros.alpha_kf[k-1][f-1]
                    *
                    (
                        self.X[k, i, t]
                        -
                        gp.quicksum(
                            self.A[k, i, t-1, f_prime]

                            for f_prime in self.conjuntos.f
                        )
                    )
                )

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for t in self.conjuntos.t
                for f in self.conjuntos.f if t != 1
            ),
            name="FallasEsperadasPorUso_general_1"
        ) if restricciones_activas[10] else None

        self.R10d = self.model.addConstrs(
            (
                self.F[k, i, t, f]
                <=
                (
                    self.parametros.alpha_kf[k-1][f-1]
                    *
                    (
                        self.X[k, i, t]
                        -
                        gp.quicksum(
                            self.A[k, i, t-1, f_prime]

                            for f_prime in self.conjuntos.f
                        )
                    )
                    +
                    0.9999999
                )

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for t in self.conjuntos.t
                for f in self.conjuntos.f if t != 1
            ),
            name="FallasEsperadasPorUso_general_2"
        ) if restricciones_activas[10] else None
        '''
        La cantidad de fallas nuevas consideradas debe ser al menos el número esperado de fallas, estimado a partir de la probabilidad de falla y la cantidad de chipeadoras operativas.
        '''

        self.R11a = self.model.addConstrs(
            (
                self.Q[k, i, 1, f]
                <=
                self.F[k, i, 1, f]

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for f in self.conjuntos.f
            ),
            name="ReparacionesFactibles_t1"
        ) if restricciones_activas[11] else None
        '''
        La cantidad de fallas reparadas en cada período no puede superar las fallas disponibles (nuevas + pendientes de reparación de períodos anteriores).
        '''

        self.R11b = self.model.addConstrs(
            (
                self.Q[k, i, t, f]
                <=
                (
                    self.A[k, i, t-1, f]
                    +
                    self.F[k, i, t, f]
                )

                for k in self.conjuntos.k
                for i in self.conjuntos.i
                for t in self.conjuntos.t if t != 1
                for f in self.conjuntos.f
            ),
            name="ReparacionesFactibles_t2"
        ) if restricciones_activas[11] else None
        '''
        La cantidad de fallas reparadas en cada período no puede superar las fallas disponibles (nuevas + pendientes de reparación de períodos anteriores).
        '''

        self.R12 = self.model.addConstrs(
            (
                gp.quicksum(
                    self.X[k, i, t]

                    for i in self.conjuntos.i
                )
                <=
                (
                    self.parametros.N_k[k-1]
                    +
                    gp.quicksum(
                        self.Z[k, tau]

                        for tau in self.conjuntos.t if tau <= t
                    )
                )

                for k in self.conjuntos.k
                for t in self.conjuntos.t
            ),
            name="DisponibilidadChipeadoras"
        ) if restricciones_activas[12] else None
        '''
        La cantidad de chipeadoras operativas de todas las zonas $i$, no puede exceder la flota total inicial más las compras acumuladas hasta el mes $t$.
        '''

        self.R13 = self.model.addConstrs(
            (
                gp.quicksum(
                    self.I[j, i, 12]

                    for j in self.conjuntos.j
                )
                <=
                self.parametros.L_i[i-1]

                for i in self.conjuntos.i
            ),
            name="ResiduosAlFinalHorizon"
        ) if restricciones_activas[13] else None
        '''
        Al final del período (12 meses), cada zona $i$ debe cumplir con un nivel máximo de residuos permitidos.
        '''

    def definir_funcion_objetivo(self):
        self.model.setObjective(
            gp.quicksum(self.parametros.CO_kt[k-1][t-1] * self.X[k, i, t]      for k in self.conjuntos.k for t in self.conjuntos.t for i in self.conjuntos.i                                          )
            + gp.quicksum(self.parametros.CT_it[i-1][t-1] * self.Y[j, i, t]                           for t in self.conjuntos.t for i in self.conjuntos.i for j in self.conjuntos.j                     )
            + gp.quicksum(self.parametros.CR_kf[k-1][f-1]              * self.Q[k, i, t, f]   for k in self.conjuntos.k for t in self.conjuntos.t for i in self.conjuntos.i                      for f in self.conjuntos.f)
            + gp.quicksum(self.parametros.h_ji[j-1][i-1]               * self.I[j, i, t]                           for t in self.conjuntos.t for i in self.conjuntos.i for j in self.conjuntos.j                     )
            + gp.quicksum(self.parametros.PC_k[k-1]                  * self.Z[k, t]         for k in self.conjuntos.k for t in self.conjuntos.t                                                               )
            + gp.quicksum(self.parametros.CC_it[i-1][t-1] * self.H[i, t]                              for t in self.conjuntos.t for i in self.conjuntos.i                                          )
            + gp.quicksum(self.parametros.CF_it[i-1][t-1] * self.D[i, t]                              for t in self.conjuntos.t for i in self.conjuntos.i                                          )
            + gp.quicksum(self.parametros.ST_it[i-1][t-1] * self.W[i, t]                              for t in self.conjuntos.t for i in self.conjuntos.i                                          ),
            sense=gp.GRB.MINIMIZE
        )

    def optimizar(self):
        self.model.Params.TimeLimit = 600
        self.model.Params.MIPGap = 0.01
        self.model.Params.LogToConsole = 1

        self.model.optimize()

    def guardar_resultados(self):
        output_path = Path(__file__).parent / "output" / self.run_name / "valores_variables.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.model.SolCount > 0:
            with output_path.open("w", encoding="utf-8") as f:
                for nombre, vars_dict in [
                    ("X", self.X),
                    ("Y", self.Y),
                    ("I", self.I),
                    ("A", self.A),
                    ("Q", self.Q),
                    ("F", self.F),
                    ("Z", self.Z),
                    ("H", self.H),
                    ("D", self.D),
                    ("W", self.W),
                ]:
                    f.write(f"{nombre}\n")
                    for key, var in vars_dict.items():
                        f.write(f"{key}: {var.X}\n")
                    f.write("\n")
        else:
            with output_path.open("w", encoding="utf-8") as f:
                f.write("No feasible solution found.\n")

        if self.model.SolCount > 0:
            resultados = leer_resultados_txt(output_path)
            generar_resumen(self.conjuntos, self.parametros, self.model, resultados, output_path.parent)
            generar_graficos_desde_txt(self.conjuntos, output_path)
