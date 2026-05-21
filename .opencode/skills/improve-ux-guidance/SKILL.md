---
name: improve-ux-guidance
description: Playbook for auditing, reviewing, and improving the User Experience (UX), form validations, tooltips, localized strings (translations.py), and interactive visualization flows. Use when the user asks to improve UI feedback, check for translation errors, design input help guides, or optimize visual calculations layouts.
---

# Improve UX and Guidance Playbook

This playbook defines the exact standards and steps to audit and improve the user interface (UI) and user experience (UX) of the Gas Flow Calc application to make it highly professional, intuitive, and instructive.

---

## Step 1 — Form Validation & On-The-Fly Feedback Audit

Professional software provides immediate, helpful feedback rather than crashing or showing pop-up blockers at the end of a long form.

### 1. Verification Checklist for Inputs
Ensure all entry inputs in `ui/panels/` use the `ValidatedEntry` widget from `ui/widgets.py`. For every input:
- **Type Safety**: Enforce proper input restriction (e.g. integer-only for fitting counts, positive float for pipe diameter/inlet pressure).
- **Physical Bounds**: Ensure the input is within realistic boundaries:
  - Inlet pressure must be $> 0$ (absolute or gauge).
  - Inlet temperature must be above cryogenic absolute zero ($> 0\text{ K}$ or $> -273.15\text{ °C}$) and below design material limit (typically $300\text{ °C}$).
  - Pipe length must be $> 0$.
- **Keystroke Hooking**: Numeric inputs must intercept invalid keystrokes (e.g. blocking letters on press).

### 2. Immediate Visual Indicators
Rather than blocking the user with standard error popups:
- Change the background of the invalid field to a soft warning color (e.g., light red/orange).
- Display a small, red validation sub-label directly under the field or update the status bar with the message from `translations.py`.
- Disable the primary calculation button *until* all inputs satisfy their validation constraints.

---

## Step 2 — Help Systems & Contextual Guidance Audit

Users should understand what each input represents and what unit is expected without consulting the documentation.

### 1. Tooltips Configuration
Ensure every input widget has a `ToolTip` bound to it. Tooltips must show:
- **Parameter Name**: Clear description of the variable.
- **Expected Unit**: E.g. "bar (gauge)", "°C", "mm", "Sm³/h".
- **Physical Bounds / Help Tip**: E.g., "Must be between 0.1 and 100 bar" or "Barlow wall thickness calculation is based on ASME B36.10M".

### 2. Gas Composition Sum Helper
When inputting custom gas mixtures:
- Display a clear, color-coded "Total Composition" label (e.g., Green if exactly $100\%$, Red/Orange if not $100\%$).
- Provide a "Normalize" button that scales the current mixture proportionally to sum to exactly $100\%$.
- List the most common natural gas compositions (e.g. Methane, Ethane, Propane) prominently for quick selection.

---

## Step 3 — Localization (i18n) & Translations Alignment

An unprofessional UI displays mixed languages or untranslated keys.

### 1. Translations Audit Protocol
Read `translations.py` and inspect both `"tr"` and `"en"` dictionaries:
- Check for **Missing Keys**: Use a regex search or static audit script to find hardcoded string literals inside `ui/panels/` or `main.py`.
- **Strict Key Mapping**: Every key in `"tr"` must exist in `"en"`.
- **Capitalization & Tone**: Turkish strings should use proper Turkish characters (`ş, ç, ğ, ı, ü, ö`) and Turkish capitalization rules. English strings should follow standard engineering terminology (e.g., "Pressure Drop" instead of "Pressure loss").

### 2. Implementation Pattern
Always replace hardcoded text with:
```python
# In ui/panels/process_panel.py
from translations import t

label = tk.Label(parent, text=t("INLET_PRESSURE"))
```

---

## Step 4 — Visual Layout & Calculation Feedback Audit

During high-intensity calculations (such as thermodynamic binary searches with thousands of CoolProp calls), the UI must remain responsive and informative.

### 1. Calculation Threading
- Ensure all heavy computations run asynchronously on a background thread.
- Provide a visual progress bar (`ttk.Progressbar`) showing active search status or phase iteration.
- Display a "Cancel" button to safely abort runaway iterations.

### 2. Phase Detection Banners
Upon calculation completion, display results with high visual hierarchy:
- Render a colored badge depending on the detected gas state:
  - **Single-Phase Gas**: Safe blue badge.
  - **Liquid Phase**: Warning purple badge (gas pipeline should not have liquid).
  - **Two-Phase Flow**: Critical orange banner (extreme risk of liquid slugging/erosion).
  - **Supercritical Flow**: Cyan badge (high pressure warning).
- Provide detailed explanation on the implications of supercritical or two-phase flow in the report panel.
- Ensure Matplotlib graphs are embedded smoothly and resize cleanly when the window is maximized.
