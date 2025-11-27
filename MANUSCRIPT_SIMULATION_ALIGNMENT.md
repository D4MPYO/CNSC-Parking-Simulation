# MANUSCRIPT vs SIMULATION ALIGNMENT REPORT
## Gaps, Inconsistencies, and Required Changes

---

## 🔴 CRITICAL ISSUES - MUST FIX

### 1. **CAPACITY MISMATCH**
**Manuscript states:** Total capacity = 237 spots
**Simulation shows:** Total capacity = 231 spots (MC=140, Cars=81, Trucks=10)

**Action Required:**
- **Update manuscript** to reflect actual capacity: 231 spots total
- OR **Update simulation** to match 237 spots
- **Recommendation:** Use simulation's 231 as ground truth since it's based on the actual map layout

**Where to fix in manuscript:**
- Section 3.2 (Study Area): Change "approximately 237 spots" → "231 spots"
- Update distribution details to "140 motorcycle spots, 81 car spots, and 10 truck spots"

---

### 2. **MONTE CARLO SIMULATION IS NOT IMPLEMENTED**
**Manuscript claims:** Uses Monte Carlo method with 1,000-10,000 iterations (Section 3.5)
**Simulation reality:** This is a DETERMINISTIC, SINGLE-RUN pygame visualization

**Major Issues:**
- No probability distributions (claims Poisson distribution in Eq. 3)
- No multiple simulation runs/iterations
- No statistical output (means, standard deviations, confidence intervals)
- No probability of full capacity calculations (Eq. 4)
- No Monte Carlo random sampling from distributions

**What the simulation ACTUALLY does:**
- Single deterministic parking visualization
- Basic random vehicle spawning using fixed rates
- Real-time animation, not statistical modeling

**Action Required:**
✅ **CREATE A SEPARATE MONTE CARLO SIMULATION MODULE** that:
1. Runs 1,000-10,000 iterations as claimed
2. Samples arrivals from Poisson distribution (λ = hourly rate)
3. Implements formulas from manuscript (Equations 1-4)
4. Calculates:
   - Average utilization rates by time
   - Probability of full capacity P(Full)
   - Standard deviations and confidence intervals
   - Peak hour statistics
5. Outputs statistical results to CSV/Excel files

---

### 3. **MISSING DATA COLLECTION METHODOLOGY**
**Manuscript claims:** "Data will be gathered every 10-15 minutes during peak hours" (Section 3.4)
**Simulation:** No data collection functionality, no logging of observations

**Action Required:**
- Add data logging functionality to record:
  - Timestamp (every 10-15 minutes simulation time)
  - Vehicle arrivals per interval
  - Vehicle departures per interval
  - Current occupancy
  - Utilization rate per zone
  - Unauthorized parking incidents
- Export to CSV format matching Table 1 requirements
- This data should feed into the Monte Carlo analysis

---

### 4. **UNAUTHORIZED/ILLEGAL PARKING**
**Manuscript mentions:** "Unauthorized Parking" as a data parameter (Table 1)
**Simulation code:** Has `PROB_ILLEGAL_PARKING = 0.50` defined but appears unused

**Where it should be used:**
- Line 72: `PROB_ILLEGAL_PARKING = 0.50` is defined
- Line 505-519: `assign_parking()` function doesn't use this probability
- Vehicles are rejected but don't illegally park

**Action Required:**
- Implement illegal parking logic:
  - When all zones full and vehicle searched MAX_SEARCH_ATTEMPTS times
  - Use `PROB_ILLEGAL_PARKING` to decide if vehicle parks illegally vs exits
  - Track illegal parking locations and counts
  - Display in UI and export in data logs

---

## ⚠️ MAJOR INCONSISTENCIES - SHOULD FIX

### 5. **PARKING DURATION FORMULA MISMATCH**
**Manuscript claims:** Random duration with exit between 3-6:30 PM
**Simulation (lines 451-459):** Exit between 3:00-6:30 PM (15.0-18.5 hours)

**Code:**
```python
target_exit = random.uniform(15.0, 18.5)  # 3:00 PM to 6:30 PM
```

**Issue:** This creates unrealistic parking durations
- Someone arriving at 7 AM stays 8-11.5 hours (reasonable)
- Someone arriving at 2 PM stays 1-4.5 hours (reasonable)
- But this is NOT how Monte Carlo should work with distributions

**Action Required:**
- Document actual parking duration distribution in manuscript
- OR implement proper duration sampling from realistic distribution (normal/exponential)
- Manuscript should describe the actual formula being used

---

### 6. **VEHICLE DISTRIBUTION MISMATCH**
**Manuscript:** Doesn't specify vehicle type distribution
**Simulation:** 76% MC, 20% Car, 4% Truck (lines 64-67)

**Action Required:**
- Add to manuscript Section 3.2 or 3.5:
  - "Vehicle composition reflects campus demographics: 76% motorcycles, 20% cars, 4% trucks"
  - Justify this distribution with observational data or campus records

---

### 7. **ARRIVAL RATES NOT DOCUMENTED**
**Manuscript:** Mentions "vehicle arrival rates per hour" but no specific numbers
**Simulation:** Specific hourly rates defined (lines 59-62):

```python
HOURLY_ARRIVAL_RATES = {
    6: 15, 7: 100, 8: 40, 9: 25, 10: 15, 11: 10,
    12: 60, 13: 30, 14: 15, 15: 8, 16: 5, 17: 2,
}
```

**Action Required:**
- Add a table to manuscript (in Section 3.3 Data Requirements or 3.5 Monte Carlo):

```latex
\begin{table}[htbp]
\caption{Hourly Vehicle Arrival Rates (vehicles/hour)}
\label{tab:arrival_rates}
\centering
\begin{tabular}{|c|c||c|c|}
\hline
Hour & Arrivals & Hour & Arrivals \\
\hline
6:00 AM & 15 & 12:00 PM & 60 \\
7:00 AM & 100 & 1:00 PM & 30 \\
8:00 AM & 40 & 2:00 PM & 15 \\
9:00 AM & 25 & 3:00 PM & 8 \\
10:00 AM & 15 & 4:00 PM & 5 \\
11:00 AM & 10 & 5:00 PM & 2 \\
\hline
\end{tabular}
\end{table}
```

---

### 8. **BATCH ARRIVALS NOT MENTIONED**
**Simulation:** Implements batch arrivals during peak hours (lines 69-71, 541-543)
- 40% probability of batch arrival during peak hours
- Batch size: 2-6 vehicles

**Action Required:**
- Add to manuscript Section 3.5:
  - "To model realistic peak-hour congestion, the simulation implements batch arrivals where groups of 2-6 vehicles arrive simultaneously with 40% probability during peak hours (7-8 AM, 12-1 PM)"

---

### 9. **PEAK HOURS DEFINITION**
**Manuscript:** "7:00-9:00 AM and after lunch" (Introduction)
**Simulation:** Peak hours = 7, 8, 12, 13 (7-8 AM, 12-1 PM) - line 445

**Issue:** Manuscript says "7-9 AM" but simulation uses "7-8 AM"

**Action Required:**
- Clarify in manuscript: Is 9 AM included in peak hours?
- OR update simulation to include hour 9 as peak

---

### 10. **SIMULATION TIME PARAMETERS**
**Manuscript:** Doesn't specify simulation duration or speed
**Simulation:**
- Runs from 6 AM to 7 PM daily (lines 28-29)
- Speed multiplier: 60x (line 30)
- Multi-day simulation (line 531)

**Action Required:**
- Add to manuscript Section 3.5:
  - "The simulation models parking dynamics from 6:00 AM to 7:00 PM daily, representing typical academic operational hours"
  - "Multiple days are simulated to capture variability in parking patterns"

---

## 📋 MISSING ELEMENTS - SHOULD ADD

### 11. **NO ZONE-SPECIFIC ANALYSIS**
**Manuscript:** Implies zone-level analysis
**Simulation:** Has individual zones but doesn't report per-zone statistics

**Action Required:**
- Add zone-specific statistics tracking:
  - Average utilization per zone
  - Time to full capacity per zone
  - Most/least utilized zones
- Add this analysis to manuscript Section 4 (Analysis Plan)

---

### 12. **NO WAIT TIME / SEARCH TIME TRACKING**
**Manuscript:** No mention of vehicles searching for parking
**Simulation:** Has search attempts (line 107) and circling behavior (lines 82, 561-570)

**Action Required:**
- Add to manuscript:
  - Document that vehicles will search up to 4 times before rejection
  - Vehicles may circle for up to 5 minutes (300 seconds)
- Track and report average search/wait times as a performance metric

---

### 13. **NO DEPARTURE RATE TRACKING**
**Manuscript:** Table 1 mentions "Vehicle Departure Rates"
**Simulation:** Tracks departures (line 558) but not as rates per time interval

**Action Required:**
- Implement departure rate calculation (departures per hour)
- Log this alongside arrival rates
- Currently only total departures are tracked

---

### 14. **VALIDATION METHOD NOT SPECIFIED**
**Manuscript:** Section 3.5 mentions "Actual observed data...will be cross-checked"
**Simulation:** No validation code or comparison metrics

**Action Required:**
- Add validation section to manuscript describing:
  - How simulation output will be validated against real observations
  - Metrics for comparing simulated vs. actual parking patterns
  - Acceptable error margins

---

## 🔧 FORMULAS IMPLEMENTATION STATUS

### Equation 1: Occupancy Calculation ✅ IMPLEMENTED
```
O(t) = O(t-1) + A(t) - D(t)
```
**Location:** Implicitly in zone tracking (lines 216-231)
**Status:** Working correctly

---

### Equation 2: Utilization Rate ✅ PARTIALLY IMPLEMENTED
```
U(t) = (O(t) / C) × 100%
```
**Location:** Line 233-234 `get_utilization()`
**Status:** Implemented per zone, but not tracked globally over time
**Need:** Time-series logging of utilization

---

### Equation 3: Poisson Distribution ❌ NOT IMPLEMENTED
```
P(A = k) = (λ^k × e^(-λ)) / k!
```
**Status:** **NOT IMPLEMENTED** - arrivals use simple probability, not Poisson
**Current method:** Line 538 `spawn_prob = arrival_rate * dt / 60.0`
**Need:** Replace with actual Poisson sampling using numpy.random.poisson()

---

### Equation 4: Probability of Full Capacity ❌ NOT CALCULATED
```
P(Full) = N_full / N_total
```
**Status:** **NOT CALCULATED** - would require Monte Carlo iterations
**Need:** Run multiple iterations and calculate this probability

---

## 📊 RECOMMENDED NEW FEATURES TO MATCH MANUSCRIPT

### Feature 1: Monte Carlo Analysis Module
Create `monte_carlo_analysis.py`:
```python
"""
Monte Carlo Parking Analysis
Runs 1,000-10,000 simulation iterations and calculates:
- Mean occupancy over time
- Probability of full capacity by hour
- 95% confidence intervals
- Standard deviations
"""
```

### Feature 2: Data Collection/Logging Module
Create `data_logger.py`:
```python
"""
Logs simulation data every 10-15 minutes (simulation time)
Exports to CSV matching Table 1 format:
- timestamp, arrivals, departures, occupancy, utilization, illegal_parking
"""
```

### Feature 3: Statistical Analysis Module
Create `statistical_analysis.py`:
```python
"""
Analyzes logged data:
- Calculates descriptive statistics
- Performs hypothesis tests
- Generates probability distributions
- Creates visualization plots
"""
```

---

## 🎯 PRIORITY ACTION ITEMS

### **IMMEDIATE (Before manuscript submission):**
1. ✅ Fix capacity numbers (237 → 231)
2. ✅ Document vehicle distribution percentages
3. ✅ Add arrival rates table
4. ✅ Clarify peak hours definition
5. ✅ Add batch arrival description

### **HIGH PRIORITY (For methodology accuracy):**
6. ⚠️ Implement actual Monte Carlo simulation with iterations
7. ⚠️ Implement Poisson distribution for arrivals
8. ⚠️ Add data logging functionality
9. ⚠️ Calculate P(Full) probability metric
10. ⚠️ Implement illegal parking behavior

### **MEDIUM PRIORITY (For completeness):**
11. 📊 Add zone-specific analysis
12. 📊 Track and report search/wait times
13. 📊 Implement departure rate tracking
14. 📊 Add validation methodology

### **LOW PRIORITY (Nice to have):**
15. 🔧 Export statistical results to Excel
16. 🔧 Generate automated plots/charts
17. 🔧 Add confidence interval calculations

---

## 📝 MANUSCRIPT SECTIONS REQUIRING UPDATES

### Section 3.2 (Study Area) - CHANGES:
- [ ] Update total capacity: 237 → 231
- [ ] Specify breakdown: MC=140, Cars=81, Trucks=10
- [ ] Add vehicle type distribution percentages

### Section 3.3 (Data Requirements) - ADDITIONS:
- [ ] Add specific hourly arrival rates table
- [ ] Clarify departure rate calculation method
- [ ] Document illegal parking tracking method

### Section 3.4 (Data Collection) - CLARIFICATIONS:
- [ ] Specify that simulation logs data every 10-15 min (simulation time)
- [ ] Describe automated vs. manual observation protocols

### Section 3.5 (Monte Carlo Simulation) - MAJOR UPDATES:
- [ ] Add batch arrival methodology
- [ ] Document search attempt limits (4 attempts max)
- [ ] Describe circling behavior (300 sec timeout)
- [ ] Add parking duration formula details
- [ ] Specify simulation runs from 6 AM - 7 PM
- [ ] Clarify number of iterations (recommend: 1,000 minimum)
- [ ] Add pseudo-code for Monte Carlo algorithm

### Section 4 (Analysis Plan) - ADDITIONS:
- [ ] Add zone-specific analysis metrics
- [ ] Include search time / wait time analysis
- [ ] Add validation metrics and methods

---

## 💻 CODE FILES TO CREATE

### 1. `monte_carlo_engine.py`
**Purpose:** True Monte Carlo simulation engine
**Features:**
- Run N iterations (1,000-10,000)
- Poisson distribution sampling
- Calculate P(Full) probabilities
- Output statistical summaries

### 2. `data_logger.py`
**Purpose:** Log simulation data
**Features:**
- Time-stamped observations
- CSV export
- Configurable intervals (10-15 min)

### 3. `statistical_analyzer.py`
**Purpose:** Post-simulation analysis
**Features:**
- Descriptive statistics
- Probability calculations
- Visualization generation

### 4. `config.py`
**Purpose:** Centralize all parameters
**Features:**
- All constants in one place
- Easy parameter tuning
- Documentation of values

---

## 📚 REFERENCES AND EQUATIONS TO ADD

Consider adding these to manuscript:

**Poisson Arrival Process:**
- Explain why Poisson is appropriate for modeling random arrivals
- Cite queueing theory literature

**Parking Duration Distribution:**
- Document whether it's uniform, normal, or exponential
- Provide statistical justification

**Validation Metrics:**
- Mean Absolute Percentage Error (MAPE)
- Root Mean Square Error (RMSE)
- Chi-square goodness of fit

---

## ✅ SUMMARY CHECKLIST

**For Manuscript to Match Current Simulation:**
- [ ] Fix capacity (237→231)
- [ ] Add vehicle distribution (76/20/4%)
- [ ] Add hourly arrival rates table
- [ ] Document batch arrivals
- [ ] Clarify peak hours (7-8 or 7-9 AM?)
- [ ] Add simulation time range (6 AM - 7 PM)
- [ ] Document search/circling behavior

**For Simulation to Match Manuscript Claims:**
- [ ] Implement TRUE Monte Carlo (multiple iterations)
- [ ] Implement Poisson distribution sampling
- [ ] Add data logging (every 10-15 min)
- [ ] Calculate P(Full) probability
- [ ] Implement illegal parking with probability
- [ ] Add statistical output (means, SD, CI)
- [ ] Add validation against real data

**For Both to Be Scientifically Sound:**
- [ ] Create separate analysis module
- [ ] Document all assumptions
- [ ] Add validation methodology
- [ ] Generate publishable results (tables/graphs)
- [ ] Ensure reproducibility

---

## 🎓 FINAL RECOMMENDATION

**You have TWO options:**

### Option A: Update Manuscript to Match Current Code
- **Pros:** Less work, code already works
- **Cons:** Cannot claim "Monte Carlo method" (misleading)
- **Best for:** Quick submission with accurate description

### Option B: Update Code to Match Manuscript (RECOMMENDED)
- **Pros:** Scientifically rigorous, publishable, matches methodology
- **Cons:** More programming work required
- **Best for:** Quality research publication

**My recommendation:** **Option B** - Create the proper Monte Carlo simulation module to match what the manuscript promises. The current pygame simulation is a great visualization tool but should be described as a "discrete-event simulation visualization" rather than a Monte Carlo analysis tool.

---

**Document created:** 2025-11-27
**Code analyzed:** CNSC_CUSTOM_MAP_SIMULATION.py (1023 lines)
**Manuscript analyzed:** LaTeX manuscript (571 lines)
