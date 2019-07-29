# Built-in modules
import numpy as np
import collections as cl
import os

# BoloCalc modules
import src.unit as un
import src.distribution as ds


class Display:
    def __init__(self, sim):
        # Store passed parameters
        self._sim = sim
        self._calcs = self._sim.calcs
        self._phys = self._sim.phys
        self._noise = self._sim.noise
        # Percentiles to be displayed
        self._pct_lo = 15.9
        self._pct_hi = 84.1

        # Merge experiment realizations
        self._merge_exps()
        # Generate table format
        self._table_format()

    # ***** Public Methods
    def sensitivity(self):
        self._init_exp_table()

        # Loop over telescopes
        self._exp_vals = {}
        for i in range(len(self._exp.tels)):
            tel = list(self._exp.tels.values())[i]
            self._init_tel_table(tel)

            # Loop over cameras
            self._tel_vals = {}
            for j in range(len(tel.cams)):
                cam = list(tel.cams.values())[j]
                self._init_cam_table(cam)

                # Loop over channels
                self._cam_vals = []
                for k in range(len(cam.chs)):
                    ch = list(cam.chs.values())[k]
                    # Write channel sensitivity
                    self._write_cam_table_row(ch, (i, j, k))

                # Write camera sensitivity
                self._finish_cam_table(cam, (i, j))

            # Write telescope sensitivity
            self._write_tel_table()

        # Write experiment sensitivity
        self._write_exp_table()

        return

    def opt_pow_tables(self):
        for i in range(len(self._exp.tels)):
            tel = list(self._exp.tels.values())[i]
            for j in range(len(tel.cams)):
                cam = list(tel.cams.values())[j]
                self._opt_f = open(
                    os.path.join(cam.dir, 'optical_power.txt'), 'w')
                for k in range(len(cam.chs)):
                    ch = list(cam.chs.values())[k]
                    self._write_opt_table(ch, (i, j, k))
                self._opt_f.close()
        return

    # ***** Helper Methods *****
    def _merge_exps(self):
        self._sns = np.concatenate(self._sim.senses, axis=-1)
        self._opts = np.concatenate(self._sim.opt_pows, axis=-1)
        self._exp = self._sim.exps[0]
        return

    def _table_format(self):
        # Camera file
        self._title_cam = ("%-10s | %-7s | %-23s | %-23s | %-23s | %-23s | "
                           "%-23s | %-23s | %-23s | %-23s | %-26s | %-26s | "
                           "%-23s | %-23s | %-23s\n"
                           % ("Chan", "Num Det",
                              "Telescope Eff", "Optical Power",
                              "Telescope Temp", "Sky Temp",
                              "Photon NEP", "Bolometer NEP", "Readout NEP",
                              "Detector NEP", "Detector NET",
                              "Detector NET_RJ",  "Array NET",
                              "Array NET_RJ", "Map Depth"))
        self._unit_cam = ("%-10s | %-7s | %-23s | %-23s | %-23s | %-23s | "
                          "%-23s | %-23s | %-23s | %-23s | %-26s | %-26s | "
                          "%-23s | %-23s | %-23s\n"
                          % ("", "", "", "[pW]", "[K_RJ]", "[K_RJ]",
                             "[aW/rtHz]", "[aW/rtHz]", "[aW/rtHz]",
                             "[aW/rtHz]", "[uK_CMB-rts]", "[uK_RJ-rts]",
                             "[uK_CMB-rts]", "[uK_RJ-rts]", "[uK_CMB-amin]"))
        self._break_cam = "-"*364+"\n"
        # Telescope and experiment files
        self._title_tel = ("%-10s | %-7s | %-23s | %-23s | %-23s\n"
                           % ("Chan", "Num Det", "Array NET",
                              "Array NET_RJ", "Map Depth"))
        self._unit_tel = ("%-10s | %-7s | %-23s | %-23s | %-23s\n"
                          % ("", "", "[uK_CMB-rts]",
                             "[uK_RJ-rts]", "[uK_CMB-amin]"))
        self._break_tel = "-"*98+"\n"
        self._title_exp = self._title_tel
        self._unit_exp = self._unit_tel
        self._break_exp = self._break_tel
        # Optical power files
        self._title_opt = ("| %-15s | %-23s | %-23s | %-23s |\n"
                           % ("Element", "Power from Sky",
                              "Power to Detect", "Cumulative Eff"))
        self._unit_opt = ("| %-15s | %-23s | %-23s | %-23s |\n"
                          % ("", "[pW]", "[pW]", ""))
        self._break_opt = "-"*97+"\n"
        return

    def _init_exp_table(self):
        self._exp_f = open(
            os.path.join(self._sim.exp_dir, 'sensitivity.txt'), 'w')
        self._exp_f.write(self._title_exp)
        self._exp_f.write(self._break_exp)
        self._exp_f.write(self._unit_exp)
        self._exp_f.write(self._break_exp)
        return

    def _init_tel_table(self, tel):
        self._tel_f = open(
            os.path.join(tel.dir, 'sensitivity.txt'), 'w')
        self._tel_f.write(self._title_tel)
        self._tel_f.write(self._break_tel)
        self._tel_f.write(self._unit_tel)
        self._tel_f.write(self._break_tel)
        return

    def _init_cam_table(self, cam):
        self._cam_f = open(os.path.join(
            cam.dir, 'sensitivity.txt'), 'w')
        self._cam_f.write(self._title_cam)
        self._cam_f.write(self._break_cam)
        self._cam_f.write(self._unit_cam)
        self._cam_f.write(self._break_cam)
        return

    def _write_cam_table_row(self, ch, tup):
        # Write channel values to camera file
        # tup (i,j,k) = (tel,cam,ch) tuple
        sns = self._sns[tup[0]][tup[1]][tup[2]]
        # Values to be stored for combining later
        ch_name = ch.param("ch_name")
        ndet = ch.param("ndet")
        net_arr = self._inv_var_spread(
            sns[9], ch, un.Unit("uK"))
        net_arr_rj = self._inv_var_spread(
            sns[11], ch, un.Unit("uK"))
        map_depth = self._map_depth(
            net_arr, ch.cam.tel)
        wstr = ("%-10s | %-7d | %-5.3f +/- (%-5.3f,%5.3f) | "
                "%-5.2f +/- (%-5.2f,%5.2f) | %-5.2f +/- (%-5.2f,%5.2f) | "
                "%-5.2f +/- (%-5.2f,%5.2f) | %-5.2f +/- (%-5.2f,%5.2f) | "
                "%-5.2f +/- (%-5.2f,%5.2f) | %-5.2f +/- (%-5.2f,%5.2f) | "
                "%-5.2f +/- (%-5.2f,%5.2f) | %-6.1f +/- (%-6.1f,%6.1f) | "
                "%-6.1f +/- (%-6.2f,%6.2f) | %-5.2f +/- (%-5.2f,%5.2f) | "
                "%-5.2f +/- (%-5.2f,%5.2f) | %-5.2f +/- (%-5.2f,%5.2f)\n"
                % (ch_name, ndet, *self._spread(sns[0]),
                   *self._spread(sns[1], un.Unit("pW")),
                   *self._spread(sns[2], un.Unit("K")),
                   *self._spread(sns[3], un.Unit("K")),
                   *self._spread(sns[4], un.Unit("aW/rtHz")),
                   *self._spread(sns[5], un.Unit("aW/rtHz")),
                   *self._spread(sns[6], un.Unit("aW/rtHz")),
                   *self._spread(sns[7], un.Unit("aW/rtHz")),
                   *self._spread(sns[8], un.Unit("uK")),
                   *self._spread(sns[10], un.Unit("uK")),
                   *net_arr, *net_arr_rj, *map_depth))
        self._cam_f.write(wstr)
        self._cam_f.write(self._break_cam)
        # Update the camera channel values
        self._cam_vals.append([
            [ndet]*3, net_arr, net_arr_rj, map_depth])
        # Update telescope channel values
        if ch_name in self._tel_vals.keys():
            self._tel_vals[ch_name] += [
                [ndet]*3, net_arr, net_arr_rj, map_depth]
        else:
            self._tel_vals[ch_name] = [[
                [ndet]*3, net_arr, net_arr_rj, map_depth]]
        # Update experiment channel values
        if ch_name in self._exp_vals.keys():
            self._exp_vals[ch_name] += [
                [ndet]*3, net_arr, net_arr_rj, map_depth]
        else:
            self._exp_vals[ch_name] = [[
                [ndet]*3, net_arr, net_arr_rj, map_depth]]
        return

    def _map_depth(self, vals, tel):
        return self._noise.sensitivity(
            vals, tel.param("fsky"), tel.param("tobs"))

    def _write_opt_table(self, ch, tup):
        # tup (i,j,k) = (tel,cam,ch) tuple
        opt = self._opts[tup[0]][tup[1]][tup[2]]
        band_name = ch.param("band_id")
        band_title = ("%s %11s %-12s %s\n"
                      % ("*"*36, ch.cam.param("cam_name"),
                         band_name, "*"*35))
        self._opt_f.write(band_title)
        self._opt_f.write(self._title_opt)
        self._opt_f.write(self._break_opt)
        self._opt_f.write(self._unit_opt)
        self._opt_f.write(self._break_opt)
        for m in range(len(ch.elem[0][0])):  # nelem
            elem_name = ch.elem[0][0][m]
            wstr = ("| %-15s | %-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.3f +/- (%-5.3f,%5.3f) |\n"
                    % (elem_name,
                       *self._spread(opt[0][m], un.Unit("pW")),
                       *self._spread(opt[1][m], un.Unit("pW")),
                       *self._spread(opt[2][m])))
            self._opt_f.write(wstr)
            self._opt_f.write(self._break_opt)
        self._opt_f.write("\n\n")
        return

    def _finish_cam_table(self, cam, tup):
        # Write cumulative sensitivity for all channels for camera
        # tup (i,j) = (tel,cam) tuple
        grouped_vals = np.concatenate(np.transpose(self._cam_vals), axis=0)
        tot_ndet = sum(grouped_vals[0::4][0])
        tot_net_arr = [self._phys.inv_var(val)
                       for val in grouped_vals[1::4]]
        tot_net_arr_rj = [self._phys.inv_var(val)
                          for val in grouped_vals[2::4]]
        tot_map_depth = [self._phys.inv_var(val)
                         for val in grouped_vals[3::4]]
        wstr = ("%-10s | %-7d | %-263s | %-5.2f +/- (%-5.2f,%5.2f) | "
                "%-5.2f +/- (%-5.2f,%5.2f) | %-5.2f +/- (%-5.2f,%5.2f)\n"
                % ("Total", tot_ndet, "",
                   *tot_net_arr,
                   *tot_net_arr_rj,
                   *tot_map_depth))
        self._cam_f.write(wstr)
        self._cam_f.close()

    def _write_tel_exp(self, val_dict, f):
        # Store totals for the telescope / experiment
        tot_det = 0
        tot_net_arr = []
        tot_net_arr_rj = []
        tot_map_depth = []
        for name, val in val_dict.items():
            # Unpack cumulative channel parameters
            grouped_vals = np.concatenate(
                np.transpose(self._cam_vals), axis=0)
            ndet_ch = sum(
                grouped_vals[0::4][0])
            net_arr_ch = [self._phys.inv_var(val)
                          for val in grouped_vals[1::4]]
            net_arr_rj_ch = [self._phys.inv_var(val)
                             for val in grouped_vals[2::4]]
            map_depth_ch = [self._phys.inv_var(val)
                            for val in grouped_vals[3::4]]
            # Write channel parameters
            wstr = ("%-10s | %-7d | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f) | "
                    "%-5.2f +/- (%-5.2f,%5.2f)\n"
                    % (name, ndet_ch, *net_arr_ch,
                       *net_arr_rj_ch, *map_depth_ch))
            f.write(wstr)
            f.write(self._break_tel)
            # Store totals
            tot_det += ndet_ch
            tot_net_arr.append(net_arr_ch)
            tot_net_arr_rj.append(net_arr_rj_ch)
            tot_map_depth.append(map_depth_ch)
        # Write the cumulative sensitivity to finish the table
        net_arr_tot = [self._sim.phys.inv_var(net)
                       for net in np.transpose(tot_net_arr)]
        net_arr_rj_tot = [self._sim.phys.inv_var(net)
                          for net in np.transpose(tot_net_arr_rj)]
        map_depth_tot = [self._sim.phys.inv_var(depth)
                         for depth in np.transpose(tot_map_depth)]
        wstr = ("%-10s | %-7d | "
                "%-5.2f +/- (%-5.2f,%5.2f) | "
                "%-5.2f +/- (%-5.2f,%5.2f) | "
                "%-5.2f +/- (%-5.2f,%5.2f)\n"
                % ("Total", tot_det, *net_arr_tot,
                   *net_arr_rj_tot, *map_depth_tot))
        f.write(wstr)
        f.close()
        return

    def _write_tel_table(self):
        return self._write_tel_exp(self._tel_vals, self._tel_f)

    def _write_exp_table(self):
        return self._write_tel_exp(self._exp_vals, self._exp_f)

    def _spread(self, inp, unit=None):
        if unit is None:
            unit = un.Unit("NA")
        lo, med, hi = unit.from_SI(np.percentile(
            inp, (self._pct_lo, 0.50, self._pct_hi)))
        return [med, abs(hi-med), abs(med-lo)]

    def _sum_spread(self, inp, unit=None):
        if unit is None:
            unit = un.Unit("NA")
        lo, med, hi = unit.from_SI(np.percentile(
            inp, (self._pct_lo, 0.50, self._pct_hi), axis=-1))
        return (np.sum(med),
                np.sqrt(np.sum((hi-med)**2)),
                np.sqrt(np.sum((med-lo)**2)))

    def _inv_var_spread(self, inp, ch, unit=None):
        if unit is None:
            unit = un.Unit("NA")
        lo, med, hi = unit.from_SI(np.percentile(
            inp, (self._pct_lo, 0.50, self._pct_hi), axis=-1))
        med_ret = self._noise.NET_arr(med, ch.param("ndet"), ch.param("yield"))
        hi_ret = (
            self._noise.NET_arr(
                hi, ch.param("ndet"), ch.param("yield")) - med_ret)
        lo_ret = (
            med_ret - self._noise.NET_arr(
                lo, ch.param("ndet"), ch.param("yield")))
        return [med_ret, hi_ret, lo_ret]
