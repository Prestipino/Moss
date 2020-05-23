import numpy as np
from peak_shape import (PseudoVoigtModel, LorentzianModel, GaussianModel,
                        DPseudoVoigtModel, DLorentzianModel, DGaussianModel,
                        HDPseudoVoigtModel, HDLorentzianModel, HDGaussianModel,
                        HPseudoVoigtModel, HLorentzianModel, HGaussianModel)
from lmfit.models import LinearModel

from functools import reduce

c_ln2 = np.log(2.0)
c_ln2pi = c_ln2 / np.pi

FitModel = LinearModel(prefix='bkg_')
FitModel.set_param_hint('bkg_intercept', value=0)
FitModel.set_param_hint('bkg_slope', value=0, vary=False)
FitParams = FitModel.make_params()


def pre2mod(sprefix):
    prefixl = [i.prefix for i in FitModel.components]
    return FitModel.components[prefixl.index(sprefix)]


def add_comp(PS, MULT, MAG, prefix, center, maxi, H, **kwargs):
    global FitModel, FitParams
    prefixl = [i.prefix for i in FitModel.components]
    if prefix in prefixl:
        print('prefix already used \n Please change')
        return

    if PS == "PseudoVoig":
        if MAG == 'sextet':
            if MULT == 'singlet':
                Smod_type = HPseudoVoigtModel
            elif MULT == 'doublet':
                Smod_type = HDPseudoVoigtModel
        elif MAG == 'singlet':
            if MULT == 'singlet':
                Smod_type = PseudoVoigtModel
            elif MULT == 'doublet':
                Smod_type = DPseudoVoigtModel
    if PS == "Lorentzian":
        if MAG == 'sextet':
            if MULT == 'singlet':
                Smod_type = HLorentzianModel
            elif MULT == 'doublet':
                Smod_type = HDLorentzianModel
        elif MAG == 'singlet':
            if MULT == 'singlet':
                Smod_type = LorentzianModel
            elif MULT == 'doublet':
                Smod_type = DLorentzianModel
    if PS == "Lorentzian":
        if MAG == 'sextet':
            if MULT == 'singlet':
                Smod_type = HGaussianModel
            elif MULT == 'doublet':
                Smod_type = HDGaussianModel
        elif MAG == 'singlet':
            if MULT == 'singlet':
                Smod_type = GaussianModel
            elif MULT == 'doublet':
                Smod_type = DGaussianModel

    mod = Smod_type.fromAdd(maxi, center, H, prefix, **kwargs)
    FitModel += mod
    FitParams += FitModel.make_params()


def remove_comp(sprefix):
    global FitParams, FitModel
    if sprefix == 'bkg_':
        print('backgroung could not removed')
        return

    comps = FitModel.components[:]
    index = [i.prefix for i in comps].index(sprefix)
    del comps[index]
    FitModel = reduce(lambda x, y: x + y, comps)
    FitParams = FitModel.make_params()
    print(FitModel)


def FitModelEval(x, params=None):
    if params is None:
        FitParam = FitModel.make_params()
        params = FitParam
    return FitModel.eval(x=x, params=params)


def Fit(y, x, yerr):
    global FitParams, FitModel
    out = FitModel.fit(y, FitModel.make_params(), x=x, weights=1 / yerr)
    FitParams = out.params
    for par_n, val in out.best_values.items():
        FitModel.set_param_hint(par_n, value=val)
    return out


def setconstrain(par_n, expr=None):
    global FitModel
    FitModel.set_param_hint(par_n, expr=expr)
    # for i, j in FitModel.param_hints.items():
    #     print(i, j)
    # print('\n'*5)
    # for i, j in FitModel.make_params().items():
    #     print(i, j)


def setvalue(par_n, expr):
    global FitModel
    FitModel.set_param_hint(par_n, value=expr)


def setlimit(par_n, minmax, value):
    global FitModel
    FitModel.param_hint[par_n][minmax] = value


def printParams():
    global FitModel
    print('\n' * 2)
    print('#' * 5)
    for i in FitModel.make_params().values():
        print(i)
    print('#' * 5)
    print('\n' * 2)


def loadFitmodel(info):
    global FitModel
    FitModel = info[0][0]
    for comp in info[0][1:]:
        FitModel + comp
    FitModel.param_hints = info[2]

