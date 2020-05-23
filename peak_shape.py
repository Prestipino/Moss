import numpy as np
import matplotlib.pyplot as plt

from lmfit.model import Model
# from lmfit.models import LinearModel

c_ln2 = np.log(2.0)
c_ln2pi = c_ln2 / np.pi
c_s2pi = np.sqrt(2 * np.pi)
c_sln2pi = np.sqrt(c_ln2pi)


def gaussian(x, amplitude=1.0, center=0.0, H=1.0):
    """1 dimensional gaussian:
    gaussian(x, amplitude, center, FWHM)
    """
    ag = 2 * c_sln2pi / H
    bg = 4 * c_ln2 / H**2
    x1 = 1.0 * x - center
    return amplitude * ag * np.exp(-bg * x1**2)


def lorentzian(x, amplitude=1.0, center=0.0, H=1.0):
    """1 dimensional lorentzian
    lorentzian(x, amplitude, center, FWHM)
    """
    gamma = H / 2.0
    return (amplitude / (1 + ((x - center) / gamma)**2)) /(np.pi * gamma)


def pvoigt(x, amplitude=1.0, center=0.0, H=1.0, Nu=0.5):
    """1 dimensional pseudo-voigt:
    pvoigt(x, amplitude, center, FWHM, fraction)
       = amplitude*(1-fraction)*gaussion(x, center, sigma_g) +
         amplitude*fraction*lorentzian(x, center, sigma)

    where sigma_g (the sigma for the Gaussian component) is

        sigma_g = sigma / sqrt(2*log(2)) ~= sigma / 1.17741

    so that the Gaussian and Lorentzian components have the
    same FWHM of 2*sigma.
    """
    return ((1.0 - Nu) * gaussian(x, amplitude, center, H) +
            Nu * lorentzian(x, amplitude, center, H))


def dpeak(peaktype, x, qs=0, amplitude=-1.0, center=0.0, H=1.0, Nu=0.5):
    amplitude *= 0.5
    qs *= 0.5
    if peaktype == 'pvoigt':
        y = pvoigt(x, amplitude=amplitude, center=center - qs, H=H, Nu=Nu)
        y += pvoigt(x, amplitude=amplitude, center=center + qs, H=H, Nu=Nu)
        return y
    if peaktype == 'gaussian':
        y = gaussian(x, amplitude=amplitude, center=center - qs, H=H)
        y += gaussian(x, amplitude=amplitude, center=center + qs, H=H)
        return y
    if peaktype == 'lorentzian':
        y = lorentzian(x, amplitude=amplitude, center=center - qs, H=H)
        y += lorentzian(x, amplitude=amplitude, center=center + qs, H=H)
        return y


def hpeak(peaktype, x, qs=0, ms=0, amplitude=-1.0, center=0.0, H=1.0, Nu=0.5):
    amplitude *= np.array([3, 2, 1, 1, 2, 3]) / 12
    hsl = np.array([- 2.5, -1.5, -0.5, 0.5, 1.5, 2.5]) * ms
    qsl = np.array([-0.5, 0.5, 0.5, -0.5, -0.5, 0.5]) * qs
    center += hsl + qsl
    y = 0
    if peaktype == 'pvoigt':
        for cen_i, amps_i in zip([center, amplitude]):
            y += pvoigt(x, amplitude=amps_i, center=cen_i, H=H, Nu=Nu)
    elif peaktype == 'gaussian':
        for cen_i, amps_i in zip([center, amplitude]):
            y += gaussian(x, amplitude=amps_i, center=cen_i, H=H)
    elif peaktype == 'lorentzian':
        for cen_i, amps_i in zip([center, amplitude]):
            y += lorentzian(x, amplitude=amps_i, center=cen_i, H=H)
    return y

# ##########       Model Classes      #################

class iPModel(Model):

    @classmethod
    def fromAdd(cls, maxi, center, H, prefix, **kwargs):
        mod = cls(prefix=prefix)
        amplitude = maxi / mod.topm(H)
        mod.set_param_hint('amplitude', value=amplitude, max=0)
        mod.set_param_hint('H', value=H, min=0)
        mod.set_param_hint('center', value=center)
        for name, value in kwargs.items():
            mod.set_param_hint(name, value=value, min=0)
        return mod

    def iplot(self, x, canvas=None):
        pars = self.make_params()
        y = self.eval(x=x, params=pars)
        if hasattr(self, 'line'):
            self.line.set_ydata(y)
        else:
            self.line, = canvas.ax.plot(x, y, picker=5, label=self.prefix)
            canvas.ax.legend()


class PseudoVoigtModel(iPModel, Model):
    def __init__(self, *args, **kwargs):
        super(PseudoVoigtModel, self).__init__(pvoigt, *args, **kwargs)
        self.set_param_hint('Nu', value=0.5, min=0.0, max=1.0)

    def topm(self, H=None, Nu=None):
        if H is None:
            H = self.param_hints['H']['value']
        if Nu is None:
            Nu = self.param_hints['Nu']['value']
        return Nu * (2 / (H * np.pi)) + (1 - Nu) * (2 * c_sln2pi / H)


class LorentzianModel(iPModel, Model):
    def __init__(self, *args, **kwargs):
        super(LorentzianModel, self).__init__(lorentzian, *args, **kwargs)

    def topm(self, H):
        if H is None:
            H = self.param_hints['H']['value']
        return 2 / (H * np.pi)


class GaussianModel(iPModel, Model):
    def __init__(self, *args, **kwargs):
        super(GaussianModel, self).__init__(gaussian, *args, **kwargs)

    def topm(self, H):
        if H is None:
            H = self.param_hints['H']['value']
        return 2 * c_sln2pi / H


class DPseudoVoigtModel(iPModel, Model):
    __t = PseudoVoigtModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 2

    def __init__(self, *args, **kwargs):
        def Pfun(x, qs=0.0, amplitude=1.0, center=0.0, H=1.0, Nu=0.5):
            return dpeak(peaktype='pvoigt', x=x, qs=qs, amplitude=amplitude,
                         center=center, H=H, Nu=Nu)
        super(DPseudoVoigtModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('Nu', value=0.5, min=0.0, max=1.0)
        self.set_param_hint('qs', value=1.0, min=0.0)


class DLorentzianModel(iPModel, Model):
    __t = LorentzianModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 2

    def __init__(self, *args, **kwargs):
        def Pfun(x, qs=0, amplitude=1.0, center=0.0, H=1.0):
            return dpeak('lorentzian', x, qs, amplitude, center, H)
        super(DLorentzianModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('qs', value=0.0, min=0.0)


class DGaussianModel(iPModel, Model):
    __t = GaussianModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 2

    def __init__(self, *args, **kwargs):
        def Pfun(x, qs=0, amplitude=1.0, center=0.0, H=1.0):
            return dpeak('gaussian', x, qs, amplitude, center, H0)
        super(DGaussianModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('qs', value=0.0, min=0.0)


class HPseudoVoigtModel(iPModel, Model):
    __t = PseudoVoigtModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 4

    def __init__(self, *args, **kwargs):
        def Pfun(x, ms=0.0, amplitude=1.0, center=0.0, H=1.0, Nu=0.5):
            return hpeak(peaktype='pvoigt', x=x, ms=ms,
                         amplitude=amplitude, center=center, H=H, Nu=Nu)
        super(HPseudoVoigtModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('Nu', value=0.5, min=0.0, max=1.0)
        self.set_param_hint('ms', value=0.0, min=0.0)


class HLorentzianModel(iPModel, Model):
    __t = LorentzianModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 4

    def __init__(self, *args, **kwargs):
        def Pfun(x, ms=0.0, amplitude=1.0, center=0.0, H=1.0):
            return hpeak('lorentzian', x=x, ms=ms, amplitude=amplitude,
                         center=center, H=H)
        super(HLorentzianModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('ms', value=0.0, min=0.0)


class HGaussianModel(iPModel, Model):
    __t = GaussianModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 4

    def __init__(self, *args, **kwargs):
        def Pfun(x, ms=0.0, amplitude=1.0, center=0.0, H=1.0):
            return hpeak('gaussian', x=x, ms=ms, amplitude=amplitude,
                         center=center, H=H)
        super(HGaussianModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('ms', value=0.0, min=0.0)


class HDPseudoVoigtModel(iPModel, Model):
    __t = PseudoVoigtModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 4

    def __init__(self, *args, **kwargs):
        def Pfun(x, qs=0.0, ms=0.0, amplitude=1.0, center=0.0, H=1.0, Nu=0.5):
            return hpeak(peaktype='pvoigt', x=x, qs=qs, ms=ms,
                         amplitude=amplitude, center=center, H=H, Nu=Nu)
        super(HPseudoVoigtModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('Nu', value=0.5, min=0.0, max=1.0)
        self.set_param_hint('qs', value=1.0, min=0.0)
        self.set_param_hint('ms', value=0.0, min=0.0)


class HDLorentzianModel(iPModel, Model):
    __t = LorentzianModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 4

    def __init__(self, *args, **kwargs):
        def Pfun(x, qs=0, ms=0.0, amplitude=1.0, center=0.0, H=1.0):
            return hpeak('lorentzian', x=x, qs=qs, ms=ms, amplitude=amplitude,
                         center=center, H=H)
        super(HLorentzianModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('qs', value=0.0, min=0.0)
        self.set_param_hint('ms', value=0.0, min=0.0)


class HDGaussianModel(iPModel, Model):
    __t = GaussianModel.topm

    def topm(self, *args, **kwargs):
        return self.__t(*args, **kwargs) / 4

    def __init__(self, *args, **kwargs):
        def Pfun(x, qs=0, ms=0.0, amplitude=1.0, center=0.0, H=1.0):
            return hpeak('gaussian', x=x, qs=qs, ms=ms, amplitude=amplitude,
                         center=center, H=H)
        super(HGaussianModel, self).__init__(Pfun, *args, **kwargs)
        self.set_param_hint('qs', value=0.0, min=0.0)
        self.set_param_hint('ms', value=0.0, min=0.0)
