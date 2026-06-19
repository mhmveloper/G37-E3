from model import OptiModel
from conjuntos_y_parametros import ParametrosEnum

if __name__ == "__main__":
    model = OptiModel()
    model = OptiModel(parametro_variado=ParametrosEnum.P, escala=0.8)
    model = OptiModel(parametro_variado=ParametrosEnum.P, escala=1.2)
    model = OptiModel(parametro_variado=ParametrosEnum.TT, escala=0.75)
    model = OptiModel(parametro_variado=ParametrosEnum.TT, escala=0.5)
    model = OptiModel(parametro_variado=ParametrosEnum.alpha, escala=0.8)
    model = OptiModel(parametro_variado=ParametrosEnum.alpha, escala=1.2)
    model = OptiModel(parametro_variado=ParametrosEnum.h, escala=0.85)
    model = OptiModel(parametro_variado=ParametrosEnum.h, escala=1.15)
    model = OptiModel(parametro_variado=ParametrosEnum.G, escala=0.8)
    model = OptiModel(parametro_variado=ParametrosEnum.G, escala=1.2)