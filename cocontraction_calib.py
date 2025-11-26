import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

# ==========================================
# 1. 설정 및 데이터 로드
# ==========================================
filename = "kty_cci_standup.txt"

try:
    data = pd.read_csv(filename, sep=r'\s+', engine='python')
except FileNotFoundError:
    print(f"Error: '{filename}' 파일을 찾을 수 없습니다.")
    exit()

p_dorsi = data['pMMG2'].values
p_plantar = data['pMMG1'].values
angle = data['Ankle_Angle'].values

# 60Hz 반영
fs = 60  
time = np.arange(len(p_dorsi)) / fs

# ==========================================
# 2. 이벤트 감지
# ==========================================
MIN_DIST_SAMPLES = int(1.0 * fs) 
PEAK_PROMINENCE = 0.3            

def detect_events(signal, angle_sig):
    sig_min, sig_max = np.min(signal), np.max(signal)
    
    # 1) MVIC (Peak)
    height_th = sig_min + 0.6 * (sig_max - sig_min)
    peaks, _ = find_peaks(signal, height=height_th, distance=MIN_DIST_SAMPLES, prominence=PEAK_PROMINENCE)
    
    # 2) Rest (Stable Window)
    w_size = int(0.5 * fs)
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
            if len(peaks) > 0 and np.min(np.abs(peaks - center)) < fs: continue
            rest_indices.append(center)
            
    return peaks, np.array(rest_indices)

mvic_idx, rest_idx = detect_events(p_plantar, angle)

# 데이터 추출
angle_relax, angle_mvic = angle[rest_idx], angle[mvic_idx]
p_dorsi_relax, p_dorsi_mvic = p_dorsi[rest_idx], p_dorsi[mvic_idx]
p_plantar_relax, p_plantar_mvic = p_plantar[rest_idx], p_plantar[mvic_idx]

# ==========================================
# 3. [수정됨] 디버그용 Time Plot (Multi-signal)
# ==========================================
fig, ax1 = plt.subplots(figsize=(14, 6))

# --- Left Axis: Muscle Signals (Stiffness/Pressure) ---
color_pf = 'black'
color_df = 'magenta'

ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Muscle Signal', color='black')

# 1) Plantar (Main Detection Source)
ax1.plot(time, p_plantar, color=color_pf, alpha=0.6, linewidth=1.5, label='p_plantar (Source)')
# Markers
ax1.plot(time[mvic_idx], p_plantar[mvic_idx], 'r*', markersize=12, label='Detected Max')
ax1.plot(time[rest_idx], p_plantar[rest_idx], 'bo', markersize=8, label='Detected Rest')

# 2) Dorsi (Reference)
ax1.plot(time, p_dorsi, color=color_df, alpha=0.5, linestyle='--', label='p_dorsi')

ax1.tick_params(axis='y', labelcolor='black')
ax1.grid(True, which='major', linestyle='--', alpha=0.5)

# --- Right Axis: Ankle Angle ---
ax2 = ax1.twinx()  # x축 공유
color_ang = 'green'

ax2.set_ylabel('Ankle Angle (deg)', color=color_ang)
ax2.plot(time, angle, color=color_ang, linewidth=2, alpha=0.7, label='Ankle Angle')
ax2.tick_params(axis='y', labelcolor=color_ang)

# --- Legend 통합 ---
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)

plt.title(f"Debug: Event Detection Verification (Fs={fs}Hz)")
plt.tight_layout()
plt.show()

# ==========================================
# 4. 피팅 함수 (MATLAB 로직 1:1 이식)
# ==========================================

# (1) Gaussian Model: d + a*exp(-((x-b)^2)/(2*c^2))
def gaussian_func(x, d, a, b, c):
    return d + a * np.exp(-((x - b)**2) / (2 * c**2 + 1e-9))

# (2) Exp2 Model: a*exp(b*x) + c*exp(d*x)
def double_exp_func(x, a, b, c, d):
    return a * np.exp(b * x) + c * np.exp(d * x)

def get_r2(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    return 1 - (ss_res / ss_tot) if ss_tot > 1e-9 else 0.0

def fit_matlab_style(ax, x, y, model_type, color, label):
    # 1. Data Preparation (MATLAB: x=x(:); y=y(:); valid=isfinite...)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    
    # 정렬 (Curve fit 안정성 위해)
    sort_idx = np.argsort(x)
    x = x[sort_idx]
    y = y[sort_idx]
    
    # 2. Statistics (MATLAB Logic)
    yl, yu = np.min(y), np.max(y)
    xl, xu = np.min(x), np.max(x)
    xr = xu - xl
    if xr <= 0: xr = 1.0
    
    # 3. Initialize & Bounds depending on Model
    if model_type == 'gauss':
        # --- MATLAB gaussfit_plot Logic ---
        # d0 = prctile(y,5);
        d0 = np.percentile(y, 5)
        # [ymax, imax] = max(y); a0 = max(ymax - d0, eps);
        imax = np.argmax(y)
        ymax = y[imax]
        a0 = max(ymax - d0, 1e-6)
        # b0 = x(imax);
        b0 = x[imax]
        # c0 = max(0.2*xr, 1.0);
        c0 = max(0.2 * xr, 1.0)
        
        p0 = [d0, a0, b0, c0] # 순서: d, a, b, c
        
        # Lower = [yl - abs(a0), 0, xl - xr, 0.05*xr]
        lb = [yl - abs(a0), 0, xl - xr, 0.05 * xr]
        # Upper = [yu + abs(a0), 5*max(yu,1), xu + xr, 2.0*xr]
        ub = [yu + abs(a0), 5 * max(yu, 1.0), xu + xr, 2.0 * xr]
        
        func = gaussian_func
        
    elif model_type == 'exp':
        # --- MATLAB exp2fit_plot Logic ---
        yr = yu - yl; 
        if yr <= 0: yr = max(yu, 1.0)
        
        a0 = 0.1 * yr
        c0 = max(yu - a0, 1.0)
        b0 = -0.073
        d0 = 0.0003
        
        p0 = [a0, b0, c0, d0] # 순서: a, b, c, d
        
        # Lower/Upper (MATLAB)
        lb = [0,      -0.5,   0,       0]
        ub = [5*max(yu,1), 0, 5*max(yu,1), 0.02] 
        # Python curve_fit requires low < high exactly. 
        # b: -0.5 ~ 0 (use 1e-9 for float safety if needed, strict 0 is fine usually)
        
        func = double_exp_func

    # 4. Fitting (Robust='LAR' -> loss='soft_l1')
    try:
        if len(x) < 4: raise ValueError("Not enough data")
        
        popt, _ = curve_fit(func, x, y, p0=p0, bounds=(lb, ub), loss='soft_l1', maxfev=5000)
        
        # Plotting
        x_plot = np.linspace(xl, xu, 200)
        y_plot = func(x_plot, *popt)
        ax.plot(x_plot, y_plot, color=color, linewidth=2, label=label)
        
        r2 = get_r2(y, func(x, *popt))
        
        if model_type == 'exp':
            return {'a':popt[0], 'b':popt[1], 'c':popt[2], 'd':popt[3]}, r2
        else:
            return {'d':popt[0], 'a':popt[1], 'b':popt[2], 'c':popt[3]}, r2
            
    except Exception as e:
        print(f"Fitting Failed ({label}): {e}")
        mean_val = np.mean(y) if len(y)>0 else 0
        ax.axhline(mean_val, color=color, linestyle=':', alpha=0.5)
        if model_type == 'exp': return {'a':mean_val, 'b':0, 'c':0, 'd':0}, 0
        else: return {'d':mean_val, 'a':0, 'b':0, 'c':1}, 0

# ==========================================
# 5. 시각화 및 결과 출력
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# DF Plot
ax1.plot(angle_relax, p_dorsi_relax, 'ro', alpha=0.5, label='Data Rest')
ax1.plot(angle_mvic, p_dorsi_mvic, 'r*', markersize=8, label='Data Max')
res_DR, r2_DR = fit_matlab_style(ax1, angle_relax, p_dorsi_relax, 'exp', 'darkred', 'Rest Fit')
res_DM, r2_DM = fit_matlab_style(ax1, angle_mvic, p_dorsi_mvic, 'gauss', 'salmon', 'Max Fit')
ax1.set_title(f"DF | R2(Rest)={r2_DR:.3f}, R2(Max)={r2_DM:.3f}")
ax1.legend(); ax1.grid(True)

# PF Plot
ax2.plot(angle_relax, p_plantar_relax, 'bo', alpha=0.5, label='Data Rest')
ax2.plot(angle_mvic, p_plantar_mvic, 'b*', markersize=8, label='Data Max')
res_PR, r2_PR = fit_matlab_style(ax2, angle_relax, p_plantar_relax, 'exp', 'navy', 'Rest Fit')
res_PM, r2_PM = fit_matlab_style(ax2, angle_mvic, p_plantar_mvic, 'gauss', 'cornflowerblue', 'Max Fit')
ax2.set_title(f"PF | R2(Rest)={r2_PR:.3f}, R2(Max)={r2_PM:.3f}")
ax2.legend(); ax2.grid(True)

plt.tight_layout()
plt.show()

# C++ Code Output
print('\n// ==========================================')
print('// Auto-generated Coefficients (MATLAB Logic Exact)')
print('// ==========================================')
def print_cpp(name, p, type):
    if type == 'exp':
        print(f"float a_{name} = {p['a']:.8f};")
        print(f"float b_{name} = {p['b']:.8f};")
        print(f"float c_{name} = {p['c']:.8f};")
        print(f"float d_{name} = {p['d']:.8f};")
    else:
        # Gauss (d, a, b, c) -> 매칭 주의
        print(f"float a_{name} = {p['a']:.8f};") # Amplitude
        print(f"float b_{name} = {p['b']:.8f};") # Centroid
        print(f"float c_{name} = {p['c']:.8f};") # Sigma
        print(f"float d_{name} = {p['d']:.8f};") # Offset

print("// 1. DF - Rest")
print_cpp("rest_DF", res_DR, 'exp')
print("\n// 2. DF - Cont")
print_cpp("cont_DF", res_DM, 'gauss')
print("\n// 3. PF - Rest")
print_cpp("rest_PF", res_PR, 'exp')
print("\n// 4. PF - Cont")
print_cpp("cont_PF", res_PM, 'gauss')
print('// ==========================================')