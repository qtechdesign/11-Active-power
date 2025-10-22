Purpose: Establish clear, durable instructions for building an interactive Python interface that teaches how Active Power (P) and Reactive Power (Q) interact in a generator/plant, visualized on a half-circle graph where y-axis = Active Power (P) and x-axis = Reactive Power (Q).

1) Product vision

Teach operators/engineers how governor (mechanical input) controls P and excitation (field current) controls Q.

Visualize the operating point on a P–Q plane with an upper half-circle:

𝑥
2
+
𝑦
2
=
𝑆
2
,
𝑦
≥
0
,
𝑥
 ⁣
=
 ⁣
𝑄
,
 
𝑦
 ⁣
=
 ⁣
𝑃
x
2
+y
2
=S
2
,y≥0,x=Q, y=P

where S is Apparent Power (MVA).

Provide intuitive controls (sliders/toggles) and guided scenarios (voltage support, low PF alarm, over-excitation, leading vars).

2) Core requirements (non-negotiable)

Axes: x = Q (MVAr), y = P (MW). Labels and units must always show.

Half-circle boundary: show 
𝑥
2
+
𝑦
2
=
𝑆
2
x
2
+y
2
=S
2
 (upper half only). Clip points that attempt to exceed S.

Operating point marker: single, prominent marker with numeric readout (P, Q, S, PF, φ).

Power factor lines: draw a line from origin to the point; compute

𝜙
=
atan2
⁡
(
𝑥
,
𝑦
)
=
atan2
⁡
(
𝑄
,
𝑃
)
,
𝑃
𝐹
=
cos
⁡
(
𝜙
)
=
𝑃
𝑆
.
ϕ=atan2(x,y)=atan2(Q,P),PF=cos(ϕ)=
S
P
	​

.

Sign convention: +Q = lagging/inductive, −Q = leading/capacitive (document on the chart).

Controls:

Slider P (MW) via “Governor %” (0–100 → 0–P_max).

Slider Q (MVAr) via “Excitation %” with limits ±Q_max(P) (see thermal limits).

Slider S (MVA rating) for teaching different machine sizes.

Limits:

Rating circle: 
𝑆
S fixed by machine rating.

Under/over-excitation limit curves (optional first release: approximate as vertical clamps at ±Q_thermal).

Stator current limit ≈ the circle; rotor heating ≈ Q limits.

State tooltips: show why a move is blocked (e.g., “exceeds rotor thermal limit”).

Reset & presets: buttons for “Nominal PF 0.85 lag”, “Voltage support (+Q)”, “Capacitive compensation (−Q)”.

3) Tech stack & packaging

Language: Python 3.10+

UI: Streamlit (preferred) or ipywidgets (fallback in Jupyter).

Plotting: Matplotlib (no seaborn). Responsive redraw on control changes.

Math: NumPy.

Quality: Ruff/Black, mypy (strict optional), pytest.

Structure:

pq_teach/
  app.py                 # Streamlit entrypoint
  pqplot.py              # plotting primitives (axes, circle, PF line)
  models.py              # data classes: Limits, Machine, OperatingPoint
  controllers.py         # governor/excitation transformations
  scenarios.py           # preset scenarios
  utils.py
  tests/
    test_geometry.py
    test_limits.py
  assets/
  README.md

4) UX specifics

Layout: left = controls, right = plot + numeric panel.

Numeric panel: P (MW), Q (MVAr), S (MVA), PF (±), φ (deg), I_stator pu.

Color/legend:

Half-circle (rating)

Operating point

PF ray

Regions tagged Lagging (x>0) / Leading (x<0).

Accessibility: 14+ pt fonts, gridlines, tooltips, keyboard-friendly sliders.

Education hints: collapsible callouts: “Governor ↑ → P ↑ (vertical move)”, “Excitation ↑ → Q ↑ (horizontal move)”.

5) Math model (minimal viable)

Apparent power: 
𝑆
=
𝑃
2
+
𝑄
2
S=
P
2
+Q
2
	​

 (must not exceed 
𝑆
𝑟
𝑎
𝑡
𝑒
𝑑
S
rated
	​

).

PF: 
𝑃
𝐹
=
𝑃
𝑆
PF=
S
P
	​

 (sign per P; display lag/lead via sign of Q).

Angle: 
𝜙
=
atan2
⁡
(
𝑄
,
𝑃
)
ϕ=atan2(Q,P) (note axes swapped from the usual convention).

Clamping: when user input causes 
𝑆
>
𝑆
𝑟
𝑎
𝑡
𝑒
𝑑
S>S
rated
	​

, project point to boundary:

(
𝑄
,
𝑃
)
←
𝑆
𝑟
𝑎
𝑡
𝑒
𝑑
𝑄
2
+
𝑃
2
(
𝑄
,
𝑃
)
(Q,P)←
Q
2
+P
2
	​

S
rated
	​

	​

(Q,P)

Thermal Q limit (first pass): 
∣
𝑄
∣
≤
𝑄
𝑚
𝑎
𝑥
∣Q∣≤Q
max
	​

. Future: make 
𝑄
𝑚
𝑎
𝑥
(
𝑃
)
Q
max
	​

(P) curve.

6) Controller semantics

Governor slider (0–100%) → P setpoint: linear map to 
𝑃
𝑚
𝑎
𝑥
P
max
	​

 (configurable).

Excitation slider (0–100%) → Q setpoint: 50% = 0 MVAr; 0% = −Q_max; 100% = +Q_max.

Snap-to-limit behavior: if clamped, flash a brief note (“at rating circle”).

Scenario presets (callable):

nominal_pf_085_lag() → set P,Q with PF≈0.85 lag.

voltage_support() → same P, push Q→+ zone.

capacitive_support() → same P, push Q→− zone.

7) Plot rules (matplotlib)

Single axes; equal aspect; limits x=[-S,S], y=[0,S].

Draw upper semicircle parametric: θ ∈ [0, π], x=S*cosθ, y=S*sinθ but swapped so that x→Q, y→P (use direct equation instead).

PF ray from origin to (Q,P).

Annotations at typical PF angles (e.g., 0.8 lag/lead).

Never hard-code colors if your environment enforces style; prefer default.

8) Config & constants

YAML/JSON (config.json):

{
  "S_rated_MVA": 50.0,
  "P_max_MW": 50.0,
  "Q_max_MVAr": 35.0,
  "labels": {"x": "Reactive Power Q [MVAr]", "y": "Active Power P [MW]"}
}


Provide environment override via PQT_S_RATED, PQT_P_MAX, PQT_Q_MAX.

9) Error handling & messages

Out-of-range input: clamp, then message: “Requested point exceeds MVA rating; clamped to boundary.”

Invalid config: fall back to safe defaults and display a banner.

Numerics: guard S=0 to avoid division by zero; PF undefined → show “—”.

10) Testing checklist (must pass)

Geometry: points on the circle satisfy 
𝑥
2
+
𝑦
2
=
𝑆
2
x
2
+y
2
=S
2
.

Clamping moves any 
𝑆
′
>
𝑆
S
′
>S point onto the circle (within 1e-6).

PF/φ against known cases:

P=40, Q=30, S=50 → PF=0.8, φ≈36.87°.

P=40, Q=−30 → PF=0.8 leading.

Controller maps: sliders → expected P/Q.

Limits: attempts beyond Q_max are clamped and flagged.

11) Documentation & didactics

README.md includes: 3-minute primer on P/Q/S, sign convention, controller mapping, and 3 guided exercises.

Glossary: P, Q, S, PF, φ, lagging vs leading, governor vs excitation.

Inline help: short, friendly messages (“Try increasing excitation to supply vars”).

12) Performance & portability

Target redraw < 50 ms on consumer laptop.

No GPU dependencies.

Works in VS Code + Python venv; requirements.txt pinned minor versions.

13) Security & privacy

No external telemetry.

No file I/O outside project root unless user exports a PNG of the plot.

14) Definition of Done (acceptance)

App runs with streamlit run app.py.

User can move P and Q via sliders and see the point move with constraints applied.

PF and φ update in real-time and match calculations.

Presets work and explain why they matter.

Tests green in CI (GitHub Actions).

15) Example prompts (for Cursor)

“Create models.py with dataclasses: Machine(S_rated, P_max, Q_max) and OperatingPoint(P,Q), methods for pf(), phi_deg(), and clamp_to_limits().”

“In pqplot.py, implement draw_half_circle(ax, S) and draw_operating_point(ax, P, Q) with axis labels and grid.”

“Build app.py (Streamlit): left column sliders for Governor%, Excitation%, S_rated; right column plot + numeric KPIs.”

“Add tests ensuring clamping correctness and PF calculations for (P=40,Q=30,S=50).”

16) Nice-to-have (V2+)

Voltage-PSS style hints (VAR/Volt droop slider).

Non-circular capability curve (salient-pole approximation).

Event recorder and animated trajectories (e.g., step in excitation).

Export to PNG/CSV of trajectory.

Authoritative note: This project intentionally uses the non-standard axis assignment requested by the user (x=Q, y=P). All formulas and angles are written accordingly.