import numpy as np, matplotlib.pyplot as plt, csv, os

print("ASSUMED PARAMETERS - NOT FROM LITERATURE")

# ---- Constants (all ASSUMPTION, not from literature) ----
X, Y0, Y1, DX = 200, 5, 100, 5              # grid & road (m)
DSRC, EXT, RMIN = 2, 300, 1                 # source & ext (m)
VREF, V = 70, 40                              # speed (km/h)
A_CAR, B_CAR = 100, 30                       # car source levels
A_MOTO, B_MOTO = 105, 25                     # moto source levels
Q_TOTAL, MOTO_SHARE = 1800, 0.7
Q_moto = Q_TOTAL * MOTO_SHARE
Q_car = Q_TOTAL - Q_moto
PHONE_A, PHONE_S, PHONE_SIGMA = 2.0, 1.0, 3.0
REF_SIGMA = 0.5
K, N_LIST = 8, [5,10,15,20,30,50,80]
R, IDW_P, SEED = 30, 2, 1

def lp_seg(L, V):
    return L - 20*np.log10(V)

def energy_sum(vals):
    return 10*np.log10(np.sum(10**(vals/10)))

def bilinear_interp(z, xq, yq):
    xq = np.atleast_1d(xq); yq = np.atleast_1d(yq)
    x = np.arange(0, X+DX, DX); y = np.arange(Y0, Y1+DX, DX)
    z2 = np.asarray(z).reshape(len(y), len(x))
    xq = np.clip(xq, x.min(), x.max()); yq = np.clip(yq, y.min(), y.max())
    tx = (xq - x.min()) / (x.max() - x.min()) * (x.size - 1)
    ty = (yq - y.min()) / (y.max() - y.min()) * (y.size - 1)
    lo_x = np.floor(tx).astype(int); hi_x = np.ceil(tx).astype(int)
    lo_y = np.floor(ty).astype(int); hi_y = np.ceil(ty).astype(int)
    lo_x = np.clip(lo_x, 0, x.size-2); hi_x = np.clip(hi_x, 1, x.size-1)
    lo_y = np.clip(lo_y, 0, y.size-2); hi_y = np.clip(hi_y, 1, y.size-1)
    t, u = tx - lo_x, ty - lo_y
    z_ll = z2[lo_y, lo_x]; z_lr = z2[lo_y, hi_x]
    z_rl = z2[hi_y, lo_x]; z_rr = z2[hi_y, hi_x]
    vals = (1-t)*(1-u)*z_ll + t*(1-u)*z_lr + (1-t)*u*z_rl + t*u*z_rr
    return vals if np.ndim(vals) else vals[()]

Lt = 70.0
assert abs((lp_seg(Lt,10)-lp_seg(Lt,20)) - 6.02) < 0.05
assert abs(energy_sum(np.array([Lt,Lt])) - Lt - 3.01) < 0.01

# Build truth noise map
nsrc = int(np.ceil((X + 2*EXT)/DSRC))
src_x = -EXT + DSRC/2 + np.arange(nsrc) * DSRC
src_x = src_x[src_x <= X + EXT]

xs = np.arange(0, X+DX, DX); ys = np.arange(Y0, Y1+DX, DX)
Xg, Yg = np.meshgrid(xs, ys)

Lw_c_car = A_CAR + B_CAR*np.log10(V/VREF)
Lw_c_moto = A_MOTO + B_MOTO*np.log10(V/VREF)
Lw_cp_car = Lw_c_car + 10*np.log10(Q_car/(1000*V)) + 10*np.log10(DSRC)
Lw_cp_moto = Lw_c_moto + 10*np.log10(Q_moto/(1000*V)) + 10*np.log10(DSRC)

Etot = np.zeros_like(Xg, dtype=float)
for xs_ in src_x:
    r = np.sqrt((Xg - xs_)**2 + Yg**2); r = np.maximum(r, RMIN)
    E = 10**((Lw_cp_car + Lw_cp_moto - 20*np.log10(r) - 8)/10)
    Etot += E
Truth = 10*np.log10(Etot)

plt.figure(); plt.imshow(Truth, extent=[0,X,Y0,Y1], origin='lower', aspect='auto')
plt.colorbar(label='Lp(dB)'); plt.title('True Noise Map')
plt.xlabel('x(m)'); plt.ylabel('y(m)'); plt.savefig('truth_map.png', dpi=100); plt.close()

# Experiment: RMSE vs N (raw & calibrated)
rmse_raw_mean = np.zeros(len(N_LIST)); rmse_raw_sd = np.zeros(len(N_LIST))
rmse_cal_mean = np.zeros(len(N_LIST)); rmse_cal_sd = np.zeros(len(N_LIST))

for i, N in enumerate(N_LIST):
    rms_raw = []; rms_cal = []
    for r in range(R):
        rng = np.random.default_rng(SEED + r)
        rx = rng.uniform(0, X, N); ry = rng.uniform(Y0, Y1, N)
        truth_vals = bilinear_interp(Truth, rx, ry)
        phone = PHONE_A + PHONE_S * truth_vals + rng.normal(0, PHONE_SIGMA, N)
        # Raw IDW
        d = np.sqrt((Xg[:, None, :] - rx[None, :, None])**2 + (Yg[:, None, :] - ry[None, :, None])**2)
        d[d == 0] = 1e-9; w = 1.0 / (d**IDW_P)
        wsum = np.sum(w, axis=1).reshape(Xg.shape[0], Xg.shape[1])
        idw_raw = np.sum(w * phone[None, :, None], axis=1) / wsum
        rms_raw.append(np.sqrt(np.mean((idw_raw - Truth)**2)))
        # Calibrated
        rng2 = np.random.default_rng(SEED + R + r)
        cx = rng2.uniform(0, X, K); cy = rng2.uniform(Y0, Y1, K)
        truth_c = bilinear_interp(Truth, cx, cy)
        phone_c = PHONE_A + PHONE_S * truth_c + rng2.normal(0, REF_SIGMA, K)
        std_c = truth_c + rng2.normal(0, REF_SIGMA, K)
        alpha, beta = np.polyfit(phone_c, std_c, 1)
        cal_phone = alpha * phone + beta
        d2 = np.sqrt((Xg[:, None, :] - rx[None, :, None])**2 + (Yg[:, None, :] - ry[None, :, None])**2)
        d2[d2 == 0] = 1e-9; w2 = 1.0 / (d2**IDW_P)
        w2sum = np.sum(w2, axis=1).reshape(Xg.shape[0], Xg.shape[1])
        idw_cal = np.sum(w2 * cal_phone[None, :, None], axis=1) / w2sum
        rms_cal.append(np.sqrt(np.mean((idw_cal - Truth)**2)))
    rmse_raw_mean[i] = np.mean(rms_raw); rmse_raw_sd[i] = np.std(rms_raw)
    rmse_cal_mean[i] = np.mean(rms_cal); rmse_cal_sd[i] = np.std(rms_cal)

# Save results CSV
with open('results.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['N', 'rmse_raw_mean', 'rmse_raw_sd', 'rmse_cal_mean', 'rmse_cal_sd'])
    for n, rrm, rrs, rcm, rcs in zip(N_LIST, rmse_raw_mean, rmse_raw_sd, rmse_cal_mean, rmse_cal_sd):
        w.writerow([n, rrm, rrs, rcm, rcs])

# Plot RMSE vs N
plt.figure(); plt.plot(N_LIST, rmse_raw_mean, 'o-', label='Raw RMSE')
plt.plot(N_LIST, rmse_cal_mean, 's-', label='Calibrated RMSE')
plt.fill_between(N_LIST, rmse_raw_mean - rmse_raw_sd, rmse_raw_mean + rmse_raw_sd, alpha=0.2)
plt.fill_between(N_LIST, rmse_cal_mean - rmse_cal_sd, rmse_cal_mean + rmse_cal_sd, alpha=0.2)
plt.xlabel('N'); plt.ylabel('RMSE (dB)'); plt.title('assumed parameters')
plt.legend(); plt.grid(True); plt.savefig('rmse_vs_N.png', dpi=100); plt.close()

print("Experiment complete. Output: results.csv, rmse_vs_N.png, truth_map.png")