# How to Run the Monte Carlo Simulation

## 🎯 Overview

You now have **TWO separate programs**:

1. **`CNSC_CUSTOM_MAP_SIMULATION.py`** - Pygame visualization (for presentations/demos)
2. **`monte_carlo_engine.py`** - TRUE Monte Carlo analysis (for journal manuscript)

## 📊 For Your Manuscript - Use `monte_carlo_engine.py`

This is the **scientific simulation** that matches your manuscript methodology.

### Quick Start

```bash
python monte_carlo_engine.py --iterations 1000
```

### Advanced Options

```bash
# Run 5,000 iterations (more accurate)
python monte_carlo_engine.py --iterations 5000

# Run with specific random seed (reproducible results)
python monte_carlo_engine.py --iterations 1000 --seed 42

# Save to custom directory
python monte_carlo_engine.py --iterations 1000 --output-dir my_results
```

## 📁 Output Files

After running, you'll get these CSV files in `monte_carlo_results/`:

### 1. `summary_statistics_TIMESTAMP.csv`
**Main results for your manuscript!**
- Mean arrivals, parked, rejected
- Standard deviations
- 95% Confidence Intervals
- **P(Full)** - Probability of full capacity (Equation 4)
- Peak occupancy statistics

**Use this table in your Results section!**

### 2. `iteration_results_TIMESTAMP.csv`
Individual results for each iteration:
- Iteration number
- Arrivals, parked, rejected per iteration
- Peak occupancy per iteration
- Times full per iteration

**Use this to create histograms/distributions!**

### 3. `time_series_TIMESTAMP.csv`
Detailed time series data (every 10 minutes):
- Hour by hour occupancy
- Utilization percentages
- Per-vehicle-type occupancy

**Use this to create time series plots!**

### 4. `hourly_averages_TIMESTAMP.csv`
**Aggregated statistics by time of day:**
- Mean occupancy by hour
- Standard deviation by hour
- Probability of being full by hour

**Use this to show peak hours in your manuscript!**

### 5. `config_TIMESTAMP.json`
Complete simulation configuration:
- All parameters used
- Capacity values
- Arrival rates
- Vehicle distributions

**Reference this in your Methodology section!**

## 📈 How to Use Results in Your Manuscript

### Section 4: Results

#### Table 1: Monte Carlo Simulation Summary Statistics
```
From: summary_statistics_TIMESTAMP.csv

Example content:
- Total iterations: 1,000
- Mean arrivals per day: 325.4 ± 18.2
- Mean parked: 287.6 ± 15.4
- Mean rejected: 37.8 ± 8.9
- P(Full): 0.456 (45.6% chance of reaching capacity)
```

#### Figure 1: Hourly Utilization Pattern
```
From: hourly_averages_TIMESTAMP.csv
Plot: Time (x-axis) vs Utilization % (y-axis)
Show mean ± standard deviation bands
```

#### Figure 2: Peak Hour Capacity Probability
```
From: hourly_averages_TIMESTAMP.csv
Show probability of being full by hour
Highlight 7-8 AM and 12-1 PM
```

#### Figure 3: Distribution of Daily Arrivals
```
From: iteration_results_TIMESTAMP.csv
Histogram of arrivals column
Show normal distribution fit
```

## 🔬 What the Monte Carlo Engine Does

### ✅ Implements ALL Manuscript Equations:

**Equation 1: Occupancy**
```
O(t) = O(t-1) + A(t) - D(t)
```
✅ Implemented in `SimulationState` class

**Equation 2: Utilization**
```
U(t) = (O(t) / C) × 100%
```
✅ Implemented in `utilization_percent` property

**Equation 3: Poisson Distribution**
```
P(A = k) = (λ^k × e^(-λ)) / k!
```
✅ Implemented in `generate_arrivals_poisson()` using `np.random.poisson()`

**Equation 4: Probability of Full**
```
P(Full) = N_full / N_total
```
✅ Calculated in `calculate_statistics()` as `probability_full`

### ✅ Features Matching Manuscript:

- [x] 1,000-10,000 iteration capability
- [x] Poisson distribution for arrivals
- [x] Data collection every 10 minutes
- [x] Vehicle type distribution (76% MC, 20% Car, 4% Truck)
- [x] Batch arrivals during peak hours
- [x] Statistical analysis (mean, SD, CI)
- [x] Probability calculations
- [x] CSV export for analysis
- [x] Time series tracking

## 🎨 For Presentations - Use `CNSC_CUSTOM_MAP_SIMULATION.py`

This is the **visualization tool** for demonstrations.

```bash
python CNSC_CUSTOM_MAP_SIMULATION.py
```

- Shows animated vehicles
- Interactive controls
- Real-time statistics
- Good for presentations and demos
- **NOT for statistical analysis in manuscript**

## 📝 Updating Your Manuscript

Based on the Monte Carlo results, update these sections:

### Section 3.5: Monte Carlo Simulation - ADD:
```latex
The Monte Carlo simulation was executed for 1,000 iterations,
with each iteration representing one complete operational day
(6:00 AM to 7:00 PM). Vehicle arrivals were sampled from a
Poisson distribution with hourly rate parameters λ ranging from
2 to 100 vehicles per hour, depending on the time of day.
The simulation tracked occupancy at 10-minute intervals,
recording 79 observation points per day across all iterations.
```

### Section 4: Results - ADD:
```latex
\subsection{Monte Carlo Simulation Results}

The Monte Carlo analysis, comprising 1,000 independent iterations,
yielded the following statistical measures. The mean daily vehicle
arrivals were [VALUE] ± [SD], with [VALUE] vehicles successfully
parked on average. The rejection rate averaged [VALUE]%, indicating
that [INTERPRETATION].

The probability of reaching full capacity, calculated using
Equation~\ref{eq:probability_full}, was found to be P(Full) = [VALUE],
meaning that parking facilities operate at or above capacity during
[VALUE]\% of observed time intervals. Peak utilization occurred
between 7:00-8:00 AM and 12:00-1:00 PM, with average utilization
rates exceeding [VALUE]\% during these periods.

[Table and Figures showing results...]
```

## 🚀 Recommended Workflow

### Step 1: Run Monte Carlo Analysis
```bash
python monte_carlo_engine.py --iterations 1000 --seed 42
```

### Step 2: Open CSV files in Excel/Python

### Step 3: Create figures using:
- Excel charts
- Python matplotlib/seaborn
- R ggplot2

### Step 4: Copy statistics to manuscript

### Step 5: Run pygame visualization for screenshots
```bash
python CNSC_CUSTOM_MAP_SIMULATION.py
```

### Step 6: Take screenshots of visualization for manuscript figures

## 💡 Tips

**For faster testing:**
```bash
python monte_carlo_engine.py --iterations 100
```

**For final manuscript results:**
```bash
python monte_carlo_engine.py --iterations 5000 --seed 42
```
(Use seed 42 for reproducibility)

**For comparison studies:**
Run multiple times with different parameters and compare results.

## ❓ Troubleshooting

**Q: No module named 'numpy'**
```bash
pip install numpy pandas
```

**Q: No file 'generated_parking_zones.py'**
- The engine will use default capacity values (231 total)
- This is fine for the manuscript

**Q: How many iterations should I use?**
- 1,000 = Good for testing (5-10 minutes)
- 5,000 = Better for manuscript (20-30 minutes)
- 10,000 = Best for publication (40-60 minutes)

**Q: Can I change arrival rates?**
- Yes! Edit `HOURLY_ARRIVAL_RATES` in `monte_carlo_engine.py`
- Re-run the simulation
- Compare results

## 📖 Next Steps

1. ✅ Run Monte Carlo simulation with 1,000+ iterations
2. ✅ Open CSV files and examine results
3. ✅ Create figures/tables for manuscript
4. ✅ Update manuscript sections with actual values
5. ✅ Run sensitivity analysis (optional)
6. ✅ Submit manuscript!

---

**Created:** 2025-11-27
**For:** CNSC Parking Optimization Manuscript
**Contact:** Check MANUSCRIPT_SIMULATION_ALIGNMENT.md for detailed gaps analysis
