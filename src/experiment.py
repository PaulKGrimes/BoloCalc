# Built-in modules
import numpy as np
import glob as gb
import os

# BoloCalc modules
import src.telescope as tp
import src.parameter as pr
import src.unit as un


class Experiment:
    """
    Experiment object gathers foreground parameters and contains
    a dictionary of telescope objects. It inherits the a Simulation
    object.

    Args:
    sim (src.Simulation): Simulation object

    Attributes:
    sim (src.Simulation): where the 'sim' arg is stored
    dir (str): the input directory for the experiment
    tels (dict): dictionary of src.Telescope objects
    """
    def __init__(self, sim):
        # Store passed classes
        self.sim = sim
        self._log = self.sim.log
        self._load = self.sim.load
        # Experiment directory
        self.dir = self.sim.exp_dir

        # Check whether experiment and config dirs exist
        self._check_dirs()

        # Store foreground parameter dictionary
        self._store_param_dict()

        # Store telescopes
        self._store_tels()

    # ***** Public Methods *****
    def evaluate(self):
        """ Generate param dict and telescope dict"""
        # Generate parameter values
        self._store_param_vals()
        # Evaluate telescopes
        for tel in self.tels.values():
            tel.evaluate()
        return

    def param(self, param):
        """
        Return parameter from param_vals

        Args:
        param (str): parameter name, param_vals key
        """
        return self._param_vals[param]

    def change_param(self, param, new_val):
        if self._param_dict is None:
            self._log.err(
                "Cannot change foreground parameter in %s when foregrounds "
                "are disabled" % (self.dir))
        if param not in self._param_dict.keys():
            if param in self._param_names.keys():
                return (self._param_dict[
                        self._param_names[param]].change(new_val))
            else:
                self._log.err(
                    "Parameter '%s' not understood by "
                    "Experiment.change_param()"
                    % (str(param)))
        elif param in self._param_dict.keys():
            return self._param_dict[param].change(new_val)
        else:
            self._log.err(
                "Parameter '%s' not understood by Experiment.change_param()"
                % (str(param)))

    # ***** Helper Methods *****
    def _param_samp(self, param):
        if self.sim.param("nexp"):
            return param.get_avg()
        else:
            return param.sample(nsample=1)

    def _store_param_dict(self):
        if self.sim.param("infg"):
            fgnd_file = os.path.join(self._config_dir, 'foregrounds.txt')
            params = self._load.foregrounds(fgnd_file)
            self._param_dict = {
                "dust_temp": pr.Parameter(
                    self._log, "Dust Temperature",
                    params["Dust Temperature"],
                    min=0.0, max=np.inf),
                "dust_ind": pr.Parameter(
                    self._log, "Dust Spec Index",
                    params["Dust Spec Index"],
                    min=-np.inf, max=np.inf),
                "dust_amp": pr.Parameter(
                    self._log, "Dust Amplitude",
                    params["Dust Amplitude"],
                    min=0.0, max=np.inf),
                "dust_freq": pr.Parameter(
                    self._log, "Dust Scale Frequency",
                    params["Dust Scale Frequency"],
                    min=0.0, max=np.inf),
                'sync_ind': pr.Parameter(
                    self._log, 'Synchrotron Spec Index',
                    params['Synchrotron Spec Index'],
                    min=-np.inf, max=np.inf),
                "sync_amp": pr.Parameter(
                    self._log, 'Synchrotron Amplitude',
                    params['Synchrotron Amplitude'],
                    min=0.0, max=np.inf)}
            self._param_names = {
                param.name: pid
                for pid, param in self._param_dict.items()}
        else:
            self._param_dict = None
            self._log.log("Ignoring foregrounds")
        return

    def _store_param_vals(self):
        self._param_vals = {}
        if self._param_dict is not None:
            for k in self._param_dict.keys():
                self._param_vals[k] = self._param_samp(self._param_dict[k])
        # Store other experiment parameters
        self._param_vals["exp_name"] = os.path.split(self.dir.rstrip('/'))[-1]
        return

    def _store_tels(self):
        tel_dirs = sorted(gb.glob(os.path.join(self.dir, '*' + os.sep)))
        tel_dirs = [x for x in tel_dirs
                    if 'config' not in x and 'paramVary' not in x]
        if len(tel_dirs) == 0:
            self._log.err(
                "Zero telescopes in '%s'" % (self.dir))
        tel_names = [tel_dir.split(os.sep)[-2] for tel_dir in tel_dirs]
        if len(tel_names) != len(set(tel_names)):
            self._log.err("Duplicate telescope name in '%s'" % (self.dir))
        self.tels = {}
        for i in range(len(tel_names)):
            self.tels.update({tel_names[i].strip():
                              tp.Telescope(self, tel_dirs[i])})
        return

    def _check_dirs(self):
        if not os.path.isdir(self.dir):
            self._log.err(
                "Experiment dir '%s' does not exist" % (self.dir))
        self._config_dir = os.path.join(self.dir, 'config')
        if not os.path.isdir(self._config_dir):
            self._log.err(
                "Experiment config dir '%s' does not exist"
                % (self._config_dir))
