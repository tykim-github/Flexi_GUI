"""
Calibration Processor - Processes pMMG calibration data and extracts coefficients
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
from PyQt5.QtWidgets import QWidget


class CalibrationProcessor:
    """Process calibration data and extract 16 coefficients"""
    
    def __init__(self, fs=60):
        """
        Initialize calibration processor
        
        Parameters:
            fs: Sampling frequency (default 60Hz)
        """
        self.fs = fs
        self.MIN_DIST_SAMPLES = int(1.0 * fs)
        self.PEAK_PROMINENCE = 0.3
        
        # Event detection results
        self.mvic_idx = None
        self.rest_idx = None
        
        # Extracted data
        self.angle_relax = None
        self.angle_mvic = None
        self.p_dorsi_relax = None
        self.p_dorsi_mvic = None
        self.p_plantar_relax = None
        self.p_plantar_mvic = None
        
        # Fitting results (16 coefficients)
        self.coeffs = {
            'rest_DF': {'a': 0, 'b': 0, 'c': 0, 'd': 0},
            'cont_DF': {'a': 0, 'b': 0, 'c': 0, 'd': 0},
            'rest_PF': {'a': 0, 'b': 0, 'c': 0, 'd': 0},
            'cont_PF': {'a': 0, 'b': 0, 'c': 0, 'd': 0}
        }
        
        self.r2_scores = {
            'rest_DF': 0,
            'cont_DF': 0,
            'rest_PF': 0,
            'cont_PF': 0
        }
    
    def load_and_process(self, filename):
        """
        Load data file and process calibration
        
        Parameters:
            filename: Path to txt file (tab-separated with columns: cnt, pMMG1, pMMG2, Ankle_Angle, Gamma)
        
        Returns:
            success: True if processing succeeded
        """
        try:
            # Load data
            data = pd.read_csv(filename, sep=r'\s+', engine='python')
            
            # Extract columns
            p_dorsi = data['pMMG2'].values
            p_plantar = data['pMMG1'].values
            angle = data['Ankle_Angle'].values
            
            # Detect events
            self.mvic_idx, self.rest_idx = self._detect_events(p_plantar, angle)
            
            # Extract data
            self.angle_relax = angle[self.rest_idx]
            self.angle_mvic = angle[self.mvic_idx]
            self.p_dorsi_relax = p_dorsi[self.rest_idx]
            self.p_dorsi_mvic = p_dorsi[self.mvic_idx]
            self.p_plantar_relax = p_plantar[self.rest_idx]
            self.p_plantar_mvic = p_plantar[self.mvic_idx]
            
            # Fit curves
            self._fit_all_curves()
            
            return True
        except Exception as e:
            print(f"Calibration processing error: {e}")
            return False
    
    def _detect_events(self, signal, angle_sig):
        """
        Detect MVIC (peaks) and Rest (stable windows) events
        
        Parameters:
            signal: pMMG signal (plantar)
            angle_sig: Ankle angle signal
        
        Returns:
            mvic_idx: Indices of MVIC events
            rest_idx: Indices of rest events
        """
        sig_min, sig_max = np.min(signal), np.max(signal)
        
        # 1) MVIC (Peak detection)
        height_th = sig_min + 0.6 * (sig_max - sig_min)
        peaks, _ = find_peaks(signal, height=height_th, distance=self.MIN_DIST_SAMPLES, 
                             prominence=self.PEAK_PROMINENCE)
        
        # 2) Rest (Stable window detection)
        w_size = int(0.5 * self.fs)
        s_ang = pd.Series(angle_sig)
        s_sig = pd.Series(signal)
        
        r_std = s_ang.rolling(w_size, center=True).std()
        r_mean = s_sig.rolling(w_size, center=True).mean()
        
        rest_th = sig_min + 0.4 * (sig_max - sig_min)
        mask = (r_std < 1.0) & (r_mean < rest_th)
        
        rest_indices = []
        mask_vals = mask.fillna(False).astype(int).values
        diffs = np.diff(np.hstack(([0], mask_vals, [0])))
        starts, ends = np.where(diffs==1)[0], np.where(diffs==-1)[0]
        
        for s, e in zip(starts, ends):
            if (e - s) >= w_size:
                center = (s + e) // 2
                if len(peaks) > 0 and np.min(np.abs(peaks - center)) < self.fs: 
                    continue
                rest_indices.append(center)
        
        return peaks, np.array(rest_indices)
    
    def _gaussian_func(self, x, d, a, b, c):
        """Gaussian model: d + a*exp(-((x-b)^2)/(2*c^2))"""
        return d + a * np.exp(-((x - b)**2) / (2 * c**2 + 1e-9))
    
    def _double_exp_func(self, x, a, b, c, d):
        """Exp2 model: a*exp(b*x) + c*exp(d*x)"""
        return a * np.exp(b * x) + c * np.exp(d * x)
    
    def _get_r2(self, y_true, y_pred):
        """Calculate R-squared"""
        ss_res = np.sum((y_true - y_pred)**2)
        ss_tot = np.sum((y_true - np.mean(y_true))**2)
        return 1 - (ss_res / ss_tot) if ss_tot > 1e-9 else 0.0
    
    def _fit_curve(self, x, y, model_type):
        """
        Fit curve using MATLAB-style logic
        
        Parameters:
            x: Input data (angle)
            y: Output data (pMMG)
            model_type: 'gauss' or 'exp'
        
        Returns:
            coeffs: Dictionary of coefficients
            r2: R-squared value
        """
        # Data preparation
        mask = np.isfinite(x) & np.isfinite(y)
        x = x[mask]
        y = y[mask]
        
        if len(x) < 4:
            return {'a': 0, 'b': 0, 'c': 0, 'd': 0}, 0.0
        
        # Sort data
        sort_idx = np.argsort(x)
        x = x[sort_idx]
        y = y[sort_idx]
        
        # Statistics
        yl, yu = np.min(y), np.max(y)
        xl, xu = np.min(x), np.max(x)
        xr = xu - xl
        if xr <= 0: 
            xr = 1.0
        
        # Initialize parameters and bounds
        if model_type == 'gauss':
            # Gaussian initialization
            d0 = np.percentile(y, 5)
            imax = np.argmax(y)
            ymax = y[imax]
            a0 = max(ymax - d0, 1e-6)
            b0 = x[imax]
            c0 = max(0.2 * xr, 1.0)
            
            p0 = [d0, a0, b0, c0]
            lb = [yl - abs(a0), 0, xl - xr, 0.05 * xr]
            ub = [yu + abs(a0), 5 * max(yu, 1.0), xu + xr, 2.0 * xr]
            
            func = self._gaussian_func
            
        else:  # 'exp'
            # Exponential initialization
            yr = yu - yl
            if yr <= 0: 
                yr = max(yu, 1.0)
            
            a0 = 0.1 * yr
            c0 = max(yu - a0, 1.0)
            b0 = -0.073
            d0 = 0.0003
            
            p0 = [a0, b0, c0, d0]
            lb = [0, -0.5, 0, 0]
            ub = [5*max(yu,1), 0, 5*max(yu,1), 0.02]
            
            func = self._double_exp_func
        
        # Curve fitting
        try:
            popt, _ = curve_fit(func, x, y, p0=p0, bounds=(lb, ub), 
                              loss='soft_l1', maxfev=5000)
            
            y_pred = func(x, *popt)
            r2 = self._get_r2(y, y_pred)
            
            if model_type == 'exp':
                return {'a': popt[0], 'b': popt[1], 'c': popt[2], 'd': popt[3]}, r2
            else:
                return {'d': popt[0], 'a': popt[1], 'b': popt[2], 'c': popt[3]}, r2
        except Exception as e:
            print(f"Fitting failed: {e}")
            mean_val = np.mean(y) if len(y) > 0 else 0
            if model_type == 'exp':
                return {'a': mean_val, 'b': 0, 'c': 0, 'd': 0}, 0
            else:
                return {'d': mean_val, 'a': 0, 'b': 0, 'c': 1}, 0
    
    def _fit_all_curves(self):
        """Fit all 4 curves and store coefficients"""
        # DF Rest (Exp)
        self.coeffs['rest_DF'], self.r2_scores['rest_DF'] = self._fit_curve(
            self.angle_relax, self.p_dorsi_relax, 'exp')
        
        # DF MVIC (Gauss)
        self.coeffs['cont_DF'], self.r2_scores['cont_DF'] = self._fit_curve(
            self.angle_mvic, self.p_dorsi_mvic, 'gauss')
        
        # PF Rest (Exp)
        self.coeffs['rest_PF'], self.r2_scores['rest_PF'] = self._fit_curve(
            self.angle_relax, self.p_plantar_relax, 'exp')
        
        # PF MVIC (Gauss)
        self.coeffs['cont_PF'], self.r2_scores['cont_PF'] = self._fit_curve(
            self.angle_mvic, self.p_plantar_mvic, 'gauss')
    
    def get_coefficients_list(self):
        """
        Get all 16 coefficients as a list
        
        Returns:
            List of 16 float values in order:
            [a_rest_DF, b_rest_DF, c_rest_DF, d_rest_DF,
             a_cont_DF, b_cont_DF, c_cont_DF, d_cont_DF,
             a_rest_PF, b_rest_PF, c_rest_PF, d_rest_PF,
             a_cont_PF, b_cont_PF, c_cont_PF, d_cont_PF]
        """
        return [
            self.coeffs['rest_DF']['a'], self.coeffs['rest_DF']['b'], 
            self.coeffs['rest_DF']['c'], self.coeffs['rest_DF']['d'],
            self.coeffs['cont_DF']['a'], self.coeffs['cont_DF']['b'], 
            self.coeffs['cont_DF']['c'], self.coeffs['cont_DF']['d'],
            self.coeffs['rest_PF']['a'], self.coeffs['rest_PF']['b'], 
            self.coeffs['rest_PF']['c'], self.coeffs['rest_PF']['d'],
            self.coeffs['cont_PF']['a'], self.coeffs['cont_PF']['b'], 
            self.coeffs['cont_PF']['c'], self.coeffs['cont_PF']['d']
        ]
    
    def plot_time_series(self, data_file):
        """
        Plot time series verification (external window)
        
        Parameters:
            data_file: Loaded data DataFrame or filename
        """
        try:
            if isinstance(data_file, str):
                data = pd.read_csv(data_file, sep=r'\s+', engine='python')
            else:
                data = data_file
            
            p_dorsi = data['pMMG2'].values
            p_plantar = data['pMMG1'].values
            angle = data['Ankle_Angle'].values
            time = np.arange(len(p_dorsi)) / self.fs
            
            # Create figure
            fig, ax1 = plt.subplots(figsize=(14, 6))
            
            # Left axis: Muscle signals
            color_pf = 'black'
            color_df = 'magenta'
            
            ax1.set_xlabel('Time (s)')
            ax1.set_ylabel('Muscle Signal', color='black')
            
            # Plantar
            ax1.plot(time, p_plantar, color=color_pf, alpha=0.6, linewidth=1.5, 
                    label='p_plantar (Source)')
            ax1.plot(time[self.mvic_idx], p_plantar[self.mvic_idx], 'r*', 
                    markersize=12, label='Detected Max')
            ax1.plot(time[self.rest_idx], p_plantar[self.rest_idx], 'bo', 
                    markersize=8, label='Detected Rest')
            
            # Dorsi
            ax1.plot(time, p_dorsi, color=color_df, alpha=0.5, linestyle='--', 
                    label='p_dorsi')
            
            ax1.tick_params(axis='y', labelcolor='black')
            ax1.grid(True, which='major', linestyle='--', alpha=0.5)
            
            # Right axis: Ankle Angle
            ax2 = ax1.twinx()
            color_ang = 'green'
            
            ax2.set_ylabel('Ankle Angle (deg)', color=color_ang)
            ax2.plot(time, angle, color=color_ang, linewidth=2, alpha=0.7, 
                    label='Ankle Angle')
            ax2.tick_params(axis='y', labelcolor=color_ang)
            
            # Legend
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', 
                      framealpha=0.9)
            
            plt.title(f"Debug: Event Detection Verification (Fs={self.fs}Hz)")
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Time series plot error: {e}")
    
    def plot_fitting_results(self):
        """Plot fitting results (external window)"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # DF Plot
            ax1.plot(self.angle_relax, self.p_dorsi_relax, 'ro', alpha=0.5, 
                    label='Data Rest')
            ax1.plot(self.angle_mvic, self.p_dorsi_mvic, 'r*', markersize=8, 
                    label='Data Max')
            
            # Plot fitted curves
            if self.r2_scores['rest_DF'] > 0:
                x_plot = np.linspace(np.min(self.angle_relax), 
                                    np.max(self.angle_relax), 200)
                y_plot = self._double_exp_func(x_plot, 
                                              self.coeffs['rest_DF']['a'],
                                              self.coeffs['rest_DF']['b'],
                                              self.coeffs['rest_DF']['c'],
                                              self.coeffs['rest_DF']['d'])
                ax1.plot(x_plot, y_plot, 'darkred', linewidth=2, label='Rest Fit')
            
            if self.r2_scores['cont_DF'] > 0:
                x_plot = np.linspace(np.min(self.angle_mvic), 
                                    np.max(self.angle_mvic), 200)
                y_plot = self._gaussian_func(x_plot,
                                            self.coeffs['cont_DF']['d'],
                                            self.coeffs['cont_DF']['a'],
                                            self.coeffs['cont_DF']['b'],
                                            self.coeffs['cont_DF']['c'])
                ax1.plot(x_plot, y_plot, 'salmon', linewidth=2, label='Max Fit')
            
            ax1.set_title(f"DF | R2(Rest)={self.r2_scores['rest_DF']:.3f}, "
                         f"R2(Max)={self.r2_scores['cont_DF']:.3f}")
            ax1.legend()
            ax1.grid(True)
            
            # PF Plot
            ax2.plot(self.angle_relax, self.p_plantar_relax, 'bo', alpha=0.5, 
                    label='Data Rest')
            ax2.plot(self.angle_mvic, self.p_plantar_mvic, 'b*', markersize=8, 
                    label='Data Max')
            
            # Plot fitted curves
            if self.r2_scores['rest_PF'] > 0:
                x_plot = np.linspace(np.min(self.angle_relax), 
                                    np.max(self.angle_relax), 200)
                y_plot = self._double_exp_func(x_plot,
                                              self.coeffs['rest_PF']['a'],
                                              self.coeffs['rest_PF']['b'],
                                              self.coeffs['rest_PF']['c'],
                                              self.coeffs['rest_PF']['d'])
                ax2.plot(x_plot, y_plot, 'navy', linewidth=2, label='Rest Fit')
            
            if self.r2_scores['cont_PF'] > 0:
                x_plot = np.linspace(np.min(self.angle_mvic), 
                                    np.max(self.angle_mvic), 200)
                y_plot = self._gaussian_func(x_plot,
                                            self.coeffs['cont_PF']['d'],
                                            self.coeffs['cont_PF']['a'],
                                            self.coeffs['cont_PF']['b'],
                                            self.coeffs['cont_PF']['c'])
                ax2.plot(x_plot, y_plot, 'cornflowerblue', linewidth=2, label='Max Fit')
            
            ax2.set_title(f"PF | R2(Rest)={self.r2_scores['rest_PF']:.3f}, "
                         f"R2(Max)={self.r2_scores['cont_PF']:.3f}")
            ax2.legend()
            ax2.grid(True)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Fitting plot error: {e}")
