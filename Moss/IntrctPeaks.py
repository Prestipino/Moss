import numpy as np
from .peak_shape import (PseudoVoigtModel, LorentzianModel, GaussianModel,
                         DPseudoVoigtModel, DLorentzianModel, DGaussianModel,
                         HDPseudoVoigtModel, HDLorentzianModel, HDGaussianModel,
                         HPseudoVoigtModel, HLorentzianModel, HGaussianModel)
from lmfit.models import LinearModel

from functools import reduce


c_ln2 = np.log(2.0)
c_ln2pi = c_ln2 / np.pi


class MossMod(object):
    def __init__(self, *args, **kwargs):
        self.FitModel = LinearModel(prefix='bkg_')
        self.FitModel.set_param_hint('bkg_intercept', value=0)
        self.FitModel.set_param_hint('bkg_slope', value=0, vary=False)
        self.FitParams = self.FitModel.make_params()

    def pre2mod(self, sprefix):
        prefixl = [i.prefix for i in self.FitModel.components]
        return self.FitModel.components[prefixl.index(sprefix)]

    def add_comp(self, PS, MULT, MAG, prefix, center, maxi, H, **kwargs):
        prefixl = [i.prefix for i in self.FitModel.components]
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
        self.FitModel += mod
        self.FitParams += self.FitModel.make_params()

    def remove_comp(self, sprefix):
        if sprefix == 'bkg_':
            print('backgroung could not removed')
            return

        comps = self.FitModel.components[:]
        index = [i.prefix for i in comps].index(sprefix)
        del comps[index]
        self.FitModel = reduce(lambda x, y: x + y, comps)
        self.FitParams = self.FitModel.make_params()
        print(self.FitModel)

    def FitModelEval(self, x, params=None):
        if params is None:
            self.FitParam = self.FitModel.make_params()
            params = self.FitParam
        return self.FitModel.eval(x=x, params=params)

    def Fit(self, y, x, yerr):
        out = self.FitModel.fit(y, self.FitModel.make_params(),
                                x=x, weights=1 / yerr)
        self.FitParams = out.params
        for par_n, val in out.best_values.items():
            self.FitModel.set_param_hint(par_n, value=val)
        return out

    def loadFitmodel(self, info):
        self.FitModel = info[0][0]
        for comp in info[0][1:]:
            self.FitModel + comp
        self.FitModel.param_hints = info[2]
