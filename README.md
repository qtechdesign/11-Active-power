# PQ Teach

Interactive Streamlit app that demonstrates how active power (P) and reactive power (Q) interact for a synchronous generator. The app visualizes the operating point on the non-standard P–Q plane where the x-axis is Q (MVAr) and the y-axis is P (MW).

## Features

- Adjustable machine rating (`S_rated`), governor (P) and excitation (Q) sliders with thermal clamping
- Upper half-circle plot of the MVA rating boundary with power factor ray and annotations
- Numeric panel reporting P, Q, S, PF, φ (deg), and stator current per-unit
- Scenario presets for nominal power factor, voltage support, and capacitive compensation
- Tooltips explaining why limits are enforced and how controls influence the operating point

## Running the app

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest
```

## Configuration

Default machine constants live in `config.json`. Override with environment variables:

- `PQT_S_RATED`
- `PQT_P_MAX`
- `PQT_Q_MAX`

## Educational Primer

Power triangle terms:

- P (active power, MW) — governed by mechanical input / governor
- Q (reactive power, MVAr) — governed by excitation system
- S (apparent power, MVA) — vector sum of P and Q, limited by stator current
- PF (power factor) — `P / S`; lagging when Q > 0, leading when Q < 0
- φ (electrical angle) — `atan2(Q, P)` in degrees within this unconventional axis alignment

### Guided Exercises

1. **Nominal PF 0.85 lag** — set the governor to deliver rated MW and Q such that PF ≈ 0.85 lagging.
2. **Voltage support** — increase excitation to move Q positive while maintaining P.
3. **Capacitive compensation** — reduce excitation to push Q negative while keeping P constant.

Observe how the operating point slides along horizontal (excitation) and vertical (governor) trajectories, and how the rating circle clamps the point when limits are exceeded.

