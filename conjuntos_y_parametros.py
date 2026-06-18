import gurobipy as gp
from data_getter import DataGetter

# Preparación de datos

dataPath = "datos.xlsx"
dataGetter = DataGetter(dataPath)

class Conjuntos:
    def __init__(self):
        '''
        Contiene los conjuntos del modelo.
        '''
        self.k = [value for value in range(1, 4)]
        '''Tipos de chipeadoras.'''
        self.t = [value for value in range(1, 13)]
        '''Meses del horizonte de planificación.'''
        self.i = [value for value in range(1, 4)]
        '''Zonas de trabajo.'''
        self.j = [value for value in range(1, 6)]
        '''Tipos de biomasa residual.'''
        self.f = [value for value in range(1, 9)]
        '''Tipos de fallas.'''

class Parametros:
    def __init__(self, conjuntos: Conjuntos):
        '''
        Contiene los parámetros del modelo.
        '''
        # Vectores/series por índice
        self.N_k = [value for value in dataGetter.get_column_values('inventario_inicial', "B") if value is not None]
        '''Inventario inicial de chipeadoras del tipo k.'''

        self.PC_k = [value for value in dataGetter.get_column_values("precio_compra", "B") if value is not None]
        '''Precio de compra de una chipeadora tipo k.'''

        self.Cap_k = [value for value in dataGetter.get_column_values("capacidad_máxima", "B") if value is not None]
        '''Capacidad máxima mensual de procesamiento de una chipeadora de tipo k.'''

        self.TT_i = [value for value in dataGetter.get_column_values("Cantidad_de_trabajadores_disp", "B") if value is not None]
        '''Cantidad de trabajadores disponibles inicialmente en la zona i.'''

        self.delta_k = [value for value in dataGetter.get_column_values("Trabajadores_para_op_una_chipea", "B") if value is not None]
        '''Cantidad de trabajadores requeridos para operar una chipeadora tipo k.'''

        self.L_i = [value for value in dataGetter.get_column_values("Biomasa_final_horizonte", "B") if value is not None]
        '''Nivel máximo permitido de biomasa residual total al final del horizonte en la zona i.'''

        # Tablas / matrices / tensores (multi-índice)

        self.CO_kt = [value_vector for value_vector in dataGetter.get_table_values("costo_operacional", "C", conjuntos.k) if value_vector is not None]
        '''Costo operacional de utilizar una chipeadora tipo k en el mes t.'''

        self.CT_it = [value_vector for value_vector in dataGetter.get_table_values("costo_transporte", "C", conjuntos.i) if value_vector is not None]
        '''Costo de transporte por kg de biomasa en la zona i durante el mes t.'''

        self.CR_kf = [value_vector for value_vector in dataGetter.get_table_values("Costo_de_reparación_una_chip", "C", conjuntos.k) if value_vector is not None]
        '''Costo de reparación de una chipeadora tipo k con falla f.'''

        self.alpha_kf = [value_vector for value_vector in dataGetter.get_table_values("Prob_falla_Chipeadora", "C", conjuntos.k) if value_vector is not None]
        '''Probabilidad de que una chipeadora tipo k sufra una falla tipo f durante t.'''

        self.G_jit = [value_vector for value_vector in dataGetter.get_table_values("Biomasa_residual_mesG", "D", conjuntos.j, conjuntos.i) if value_vector is not None]
        '''Biomasa residual tipo j generada en la zona i durante el mes t.'''

        self.w_ji = [value_vector for value_vector in dataGetter.get_table_values("Biomasa_residual_inicial", "C", conjuntos.j) if value_vector is not None]
        '''Cantidad inicial de biomasa residual tipo j en la zona i.'''

        self.P_it = [value_vector for value_vector in dataGetter.get_table_values("capacidad_máxima_acopio", "C", conjuntos.i) if value_vector is not None]
        '''Capacidad máxima en kg de acopio en la zona i durante el mes t.'''

        self.ST_it = [value_vector for value_vector in dataGetter.get_table_values("Sueldo_mensual_de_un_trabajador", "C", conjuntos.i) if value_vector is not None]
        '''Sueldo mensual de un trabajador en la zona i durante el mes t.'''

        self.CC_it = [value_vector for value_vector in dataGetter.get_table_values("Costo_de_contratar_un_trabajado", "C", conjuntos.i) if value_vector is not None]
        '''Costo de contratar un trabajador en la zona i durante el mes t.'''

        self.CF_it = [value_vector for value_vector in dataGetter.get_table_values("Costo_de_desvincular_trabajador", "C", conjuntos.i) if value_vector is not None]
        '''Costo de desvincular un trabajador en la zona i durante el mes t.'''

        self.h_ji = [value_vector for value_vector in dataGetter.get_table_values("Penalizacion_biomasa_residual", "E", conjuntos.j) if value_vector is not None]
        '''Penalización por kg de biomasa residual tipo j remanente en la zona i (ponderada por el riesgo de incendio de la zona respectiva)'''