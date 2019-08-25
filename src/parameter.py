# Built-in modules
import numpy as np
import sys as sy

# BoloCalc modules
import src.unit as un
import src.distribution as ds


class Parameter:
    """
    Parameter object contains attributes for input and output parameters.
    If 'inp' argument is a float, one band is assumed; if it is a list,
    len(list) bands are assumed.

    Args:
    log (src.Logging): logging object
    name (str): parameter name
    inp (str or src.Distribution): parameter value(s)
    unit (src.Unit): parameter unit. Defaults to src.Unit('NA')
    min (float): minimum allowed value. Defaults to None
    max (float): maximum allowe value. Defaults to None
    type (type): cast parameter data type. Defaults to numpy.float

    Attributes
    name (str): where the 'name' arg is stored
    unit (src.Unit): where the 'unit' arg is stored
    type (type): where the 'type' arg is stored
    """

    def __init__(self, log, name, inp, unit=None,
                 min=None, max=None, inp_type=float):
        # Store passed arguments
        self._log = log
        self.name = name
        if unit is not None:
            self.unit = unit
        elif self.name in un.std_units.keys():
            self.unit = un.std_units[self.name]
        else:
            self.unit = un.Unit("NA")
        self._min = self._float(min)
        self._max = self._float(max)
        self._type = inp_type

        # Spread delimiter
        self._spread_delim = '+/-'
        # Allowed parameter string values when input type is float
        self._float_str_vals = ["NA", "PDF", "BAND"]

        # Store the parameter value, mean, and standard deviation
        self._store_param(inp)
        # Check that the value is within the allowed range
        self._check_range()

    # ***** Public Methods *****
    def is_empty(self):
        """ Check if a parameter is 'NA' """
        if 'NA' in str(self._avg):
            return True
        else:
            return False

    def convolve(self, param):
        """
        Multiply self._avg with param.avg
        and quadrature sum self._std with param.std
        The new avg and std replace self._avg and self._std

        Args:
        param (src.Parameter): parameter to convolve with this object.
        """
        if not self.is_empty() and not param.is_empty():
            self._avg = self._avg * param.avg
            self._std = np.sqrt(self._std**2 + param.std**2)

    def multiply(self, factor):
        """
        Multiply self._avg and self._std by factor

        Args:
        factor (float): factor to multiply self._avg and self._std by
        """
        if not self.is_empty():
            self._avg = self._avg * factor
            self._std = self._std * factor

    def fetch(self, band_id=1):
        """
        Return (avg, std) given a band_id, or return (val)

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        if self._val is not None and self._avg is None:
            return (self._val, 'NA', 'NA')
        if self.is_empty():
            return ('NA', 'NA', 'NA')
        else:
            if self._mult_bands:
                return (self._avg[band_id - 1],
                        self._med[band_id - 1],
                        self._std[band_id - 1])
            else:
                return (self._avg,
                        self._med,
                        self._std)

    def change(self, new_avg, new_std=None, band_id=1):
        """
        Change self._avg to new_avg and self._std to new_std

        Args:
        new_avg (int or list): new value to be set

        Return 'True' if avg or std value was altered, 'False' if not
        """
        ret_bool = False
        if type(new_avg) is str:
            avg_new = new_avg
            if self._mult_bands:
                if self._avg[band_id-1] is not avg_new:
                    self._avg[band_id-1] = avg_new
                    ret_bool = True
                else:
                    ret_bool = False
            else:
                if self._avg is not avg_new:
                    self._avg = avg_new
                    ret_bool = True
                else:
                    ret_bool = False
        elif type(new_avg) is float or type(new_avg) is np.float_:
            avg_new = self.unit.to_SI(new_avg)
            if self.is_empty():
                if self._mult_bands:
                    self._avg[band_id-1] = avg_new
                else:
                    self._avg = avg_new
                ret_bool = True
                return ret_bool
            if self._mult_bands:
                if (self._sig_figs(avg_new, 5) !=
                   self._sig_figs(self._avg[band_id-1], 5)):
                    self._avg[band_id-1] = avg_new
                    ret_bool = True
                if new_std is not None:
                    std_new = self.unit.to_SI(new_std)
                    if (self._sig_figs(std_new, 5) !=
                       self._sig_figs(self._std[band_id-1], 5)):
                        self._std[band_id-1] = std_new
                        ret_bool = True
            else:
                if (self._sig_figs(avg_new, 5) !=
                   self._sig_figs(self._avg, 5)):
                    self._avg = avg_new
                    ret_bool = True
                if new_std is not None:
                    std_new = self.unit.to_SI(new_std)
                    if (self._sig_figs(std_new, 5) !=
                       self._sig_figs(self._std, 5)):
                        self._std = std_new
                        ret_bool = True
        else:
            self._log.err(
                "Could not change parameter '%s' to value '%s' of type '%s'"
                % (str(self.name), str(new_avg), str(type(new_avg))))
        return ret_bool

    def get_val(self):
        """ Return the input value """
        return self._val

    def get_avg(self, band_id=1):
        """
        Return average value for band_id

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        return self.fetch(band_id)[0]

    def get_med(self, band_id=1):
        """
        Return average value for band_id

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        return self.fetch(band_id)[1]
    
    def get_std(self, band_id=1):
        """
        Return standard deviation for band_id

        Args:
        band_id (int): band ID indexed from 1. Defaults to 1.
        """
        return self.fetch(band_id)[2]

    def sample(self, band_id=1, nsample=1, min=None, max=None):
        """
        Sample parameter distribution for band_id nsample times
        and return the sampled values in an array if nsample > 1
        or as a float if nsample = 1.

        Args:
        band_id (int): band ID indexes from 1. Defaults to 1.
        nsample (int): number of samples to draw from distribution
        min (float): the minimum allowed value to be returned
        max (float): the maximum allowed value to be returned
        """
        if min is None:
            min = self._min
        if max is None:
            max = self._max
        if self.is_empty():
            return 'NA'
        elif isinstance(self._val, ds.Distribution):
            return self._val.sample()
        else:
            vals = self.fetch(band_id)
            avg = vals[0]
            std = vals[2]
            if np.any(std <= 0.):
                return avg
            else:
                if nsample == 1:
                    samp = np.random.normal(avg, std, nsample)[0]
                else:
                    samp = np.random.normal(avg, std, nsample)

            if min is not None and samp < min:
                return min
            if max is not None and samp > max:
                return max
            return samp

    # ***** Private Methods *****
    def _float(self, val):
        """ Convert val to an array of or single float(s) """
        if val is None:
            self._mult_bands = False
            return None
        try:
            float_val = float(val)
            self._mult_bands = False
            return self.unit.to_SI(float_val)
        except ValueError:
            try:
                arr_val = np.array(eval(val)).astype(float)
                self._mult_bands = True
                return self.unit.to_SI(arr_val)
            except:
                self._mult_bands = False
                ret = str(val).strip().upper()
                if ret in self._float_str_vals:
                    return ret
                else:
                    self._log.err(
                        "Passed parameter '%s' with value '%s' cannot be type "
                        "casted to float" % (self.name, str(val)))

    def _zero(self, val):
        """Convert val to an array of or single zero(s)"""
        try:
            return np.zeros(len(val))
        except:
            return 0.

    def _check_range(self):
        if self._avg is None or isinstance(self._avg, str):
            return True
        else:
            avg = np.array(self._avg)
            if self._min is not None and np.any(avg < self._min):
                self._log.err(
                    "Passed value %s for parameter %s lower than the mininum \
                    allowed value %f" % (
                        str(self._avg), self.name, self._min), 0)
            elif self._max is not None and np.any(avg > self._max):
                self._log.err(
                    "Passed value %s for parameter %s greater than the maximum \
                    allowed value %f" % (
                        str(self._avg), self.name, self._max))
            else:
                return True

    def _store_param(self, inp):
        if self._type is bool:
            self._store_bool(inp)
        elif self._type is float:
            self._store_float(inp)
        elif self._type is int:
            self._store_int(inp)
        elif self._type is str:
            self._val = str(inp)
            self._avg = None
            self._med = None
            self._std = None
        elif self._type is list:
            self._val = eval(inp)
            self._avg = None
            self._med = None
            self._std = None
        else:
            self._log.err(
                "Passed paramter '%s' not one of allowed data types: \
                bool, float, int, str, list" % (self.name))
        return True

    def _sig_figs(self, inp, sig):
        if inp == 0:
            return inp
        else:
            return round(inp, sig-int(np.floor(np.log10(abs(inp))))-1)

    def _store_bool(self, inp):
        val = inp.lower().capitalize().strip()
        if val is not "True" or val is not "False":
            self._log.err(
                "Failed to parse boolean input '%s'" % (inp))
        self._mult_bands = False
        self._val = eval(val)
        self._avg = None
        self._med = None
        self._std = None
        return

    def _store_float(self, inp):
        if isinstance(inp, str):
            if self._spread_delim in inp:
                self._val = None
                vals = inp.split(self._spread_delim)
                self._avg = self._float(vals[0])
                self._med = self._avg
                self._std = self._float(vals[1])
            else:
                self._val = None
                self._avg = self._float(inp)
                self._med = self._avg
                self._std = self._zero(self._avg)
        elif isinstance(inp, ds.Distribution):
            self._val = None
            self._avg = self._float(inp.mean())
            self._med = self._float(inp.median())
            self._std = self._float(inp.std())
        return

    def _store_int(self, inp):
        try:
            self._val = None
            self._avg = int(inp)
            self._med = self._avg
            self._std = None
        except ValueError:
            self._log.err(
                    "Passed parameter '%s' with value '%s' cannot be type "
                    "casted to int" % (self.name, str(inp)))
        return