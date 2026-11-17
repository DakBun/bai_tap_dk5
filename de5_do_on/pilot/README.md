# Pilot Traffic Noise Model

## How to run
```bash
python pilot/pilot_ondo.py
```

## Output files
- **results.csv** – Contains columns `N`, `rmse_raw_mean`, `rmse_raw_sd`, `rmse_cal_mean`, `rmse_cal_sd` with average RMSE for each N in `N_LIST` over `R` iterations.
- **rmse_vs_N.png** – Plot of RMSE (raw and calibrated) against the number of phone measurements N, with error bars (±1 std dev) and title "assumed parameters".
- **truth_map.png** – Visualisation of the synthetic true noise map used as ground truth.

## ASSUMPTION constants (all dummy, not from literature)
- `X = 200` – road length parameter (m)
- `Y0 = 5` – grid y min (m)
- `Y1 = 100` – grid y max (m)
- `DX = 5` – grid step (m)
- `DSRC = 2` – source segment length (m)
- `EXT = 300` – road extension beyond ends (m)
- `RMIN = 1` – minimum distance reference (m)
- `VREF = 70` – reference speed (km/h)
- `A_CAR = 100` – car source level at 1m (dB re µPa)
- `B_CAR = 30` – car speed exponent (dB)
- `A_MOTO = 105` – moto source level at 1m (dB re µPa)
- `B_MOTO = 25` – moto speed exponent (dB)
- `V = 40` – vehicle speed (km/h)
- `Q_TOTAL = 1800` – total vehicle flow (xe/giờ)
- `MOTO_SHARE = 0.7` – motorcycle share fraction
- `Q_moto = Q_TOTAL*MOTO_SHARE` – motorcycle flow
- `Q_car = Q_TOTAL - Q_moto` – car flow
- `PHONE_A = 2.0` – phone intercept (dB)
- `PHONE_S = 1.0` – phone slope (dB)
- `PHONE_SIGMA = 3.0` – phone measurement noise std (dB)
- `REF_SIGMA = 0.5` – reference device noise std (dB)
- `K = 8` – number of calibration points
- `N_LIST = [5,10,15,20,30,50,80]` – N values examined
- `R = 30` – Monte Carlo iterations (reduced to 20 for <25s runtime if needed)
- `IDW_P = 2` – IDW power parameter
- `SEED = 1` – random seed

## Limitations
1. All constants are dummy values; the model is not calibrated against real acoustic literature.
2. The synthetic truth map is a simple constructed function and does not represent realistic urban noise propagation.
3. Phone measurements are simulated with additive Gaussian noise only; multipath, device heterogeneity, and localization errors are not included. No reflection/shielding effects from the road edge; direct dB interpolation only.