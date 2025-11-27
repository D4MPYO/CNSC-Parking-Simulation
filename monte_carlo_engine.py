"""
MONTE CARLO PARKING SIMULATION ENGINE
======================================
This is the TRUE Monte Carlo simulation for the manuscript.
Runs 1,000-10,000 iterations without visualization.
Implements actual statistical analysis using Poisson distributions.

Usage:
    python monte_carlo_engine.py --iterations 1000 --days 5
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict
import json
from datetime import datetime
import argparse

# Import configuration from main simulation
try:
    from generated_parking_zones import PARKING_ZONES
except ImportError:
    print("Warning: generated_parking_zones.py not found. Using default capacity.")
    PARKING_ZONES = []

# Calculate capacities (same as main simulation)
if PARKING_ZONES:
    TOTAL_MC_CAPACITY = sum(z["capacity"] for z in PARKING_ZONES if z["zone_type"] == "motorcycle")
    TOTAL_CAR_CAPACITY = sum(z["capacity"] for z in PARKING_ZONES if z["zone_type"] == "car")
    TOTAL_TRUCK_CAPACITY = sum(z["capacity"] for z in PARKING_ZONES if z["zone_type"] == "truck")
else:
    # Default values
    TOTAL_MC_CAPACITY = 140
    TOTAL_CAR_CAPACITY = 81
    TOTAL_TRUCK_CAPACITY = 10

TOTAL_CAPACITY = TOTAL_MC_CAPACITY + TOTAL_CAR_CAPACITY + TOTAL_TRUCK_CAPACITY

# Simulation parameters (matching main simulation)
# REALISTIC SCENARIO - Moderate congestion (adjust based on actual observations)
HOURLY_ARRIVAL_RATES = {
    6: 10,   # Early arrivals
    7: 60,   # Morning rush (7:00-8:00 AM) - ADJUST THIS based on gate counts
    8: 30,   # Mid-morning
    9: 20,   # Late morning
    10: 12,  # Before lunch
    11: 8,   # Lunch prep
    12: 40,  # Lunch time (12:00-1:00 PM) - ADJUST THIS based on observations
    13: 25,  # After lunch
    14: 10,  # Afternoon classes
    15: 5,   # Late afternoon
    16: 3,   # Going home
    17: 2,   # Almost closing
}

# ALTERNATIVE: If you observed higher congestion, use these instead:
# HOURLY_ARRIVAL_RATES = {
#     6: 15, 7: 100, 8: 40, 9: 25, 10: 15, 11: 10,
#     12: 60, 13: 30, 14: 15, 15: 8, 16: 5, 17: 2,
# }

# Vehicle distribution (76% MC, 20% Car, 4% Truck)
PROB_MOTORCYCLE = 0.76
PROB_CAR = 0.20
PROB_TRUCK = 0.04  # Explicitly define truck probability

# Peak hours
PEAK_HOURS = [7, 8, 12, 13]

# Batch arrival parameters
PROB_BATCH_ARRIVAL = 0.40
BATCH_SIZE_MIN = 2
BATCH_SIZE_MAX = 6

# Search and rejection
MAX_SEARCH_ATTEMPTS = 4
CIRCLING_TIMEOUT = 300  # seconds

# Parking duration: exit between 3:00 PM (15.0) and 6:30 PM (18.5)
EXIT_TIME_MIN = 15.0
EXIT_TIME_MAX = 18.5

# Simulation time
START_HOUR = 6
END_HOUR = 19
SIMULATION_TIME_STEP = 60  # seconds (1 minute intervals)

# Data collection interval (10-15 minutes as per manuscript)
DATA_COLLECTION_INTERVAL = 600  # 10 minutes in seconds


@dataclass
class Vehicle:
    """Simplified vehicle for Monte Carlo (no graphics needed)"""
    id: int
    type: str  # 'motorcycle', 'car', 'truck'
    arrival_time: float  # seconds from start of day
    departure_time: float  # seconds from start of day
    parked: bool = False
    rejected: bool = False
    search_attempts: int = 0
    parking_zone_type: str = None  # Which zone type it parked in


@dataclass
class SimulationState:
    """State of parking at a given time"""
    time: float  # seconds from start of day
    mc_occupied: int = 0
    car_occupied: int = 0
    truck_occupied: int = 0

    @property
    def total_occupied(self):
        return self.mc_occupied + self.car_occupied + self.truck_occupied

    @property
    def utilization_percent(self):
        return (self.total_occupied / TOTAL_CAPACITY * 100) if TOTAL_CAPACITY > 0 else 0

    @property
    def mc_utilization(self):
        return (self.mc_occupied / TOTAL_MC_CAPACITY * 100) if TOTAL_MC_CAPACITY > 0 else 0

    @property
    def car_utilization(self):
        return (self.car_occupied / TOTAL_CAR_CAPACITY * 100) if TOTAL_CAR_CAPACITY > 0 else 0

    @property
    def truck_utilization(self):
        return (self.truck_occupied / TOTAL_TRUCK_CAPACITY * 100) if TOTAL_TRUCK_CAPACITY > 0 else 0

    def is_full(self):
        """Check if ANY vehicle type has reached capacity"""
        return (self.mc_occupied >= TOTAL_MC_CAPACITY or
                self.car_occupied >= TOTAL_CAR_CAPACITY or
                self.truck_occupied >= TOTAL_TRUCK_CAPACITY)

    def is_completely_full(self):
        """Check if ALL parking is completely full"""
        return (self.mc_occupied >= TOTAL_MC_CAPACITY and
                self.car_occupied >= TOTAL_CAR_CAPACITY and
                self.truck_occupied >= TOTAL_TRUCK_CAPACITY)


@dataclass
class IterationResult:
    """Results from a single Monte Carlo iteration"""
    iteration: int
    arrivals: int = 0
    parked: int = 0
    rejected: int = 0
    peak_occupancy: int = 0
    peak_utilization: float = 0.0
    times_full: int = 0  # Number of time intervals when parking was full
    time_series: List[SimulationState] = field(default_factory=list)

    # Per vehicle type statistics
    mc_arrivals: int = 0
    car_arrivals: int = 0
    truck_arrivals: int = 0
    mc_rejected: int = 0
    car_rejected: int = 0
    truck_rejected: int = 0


class MonteCarloSimulation:
    """Monte Carlo simulation engine for parking analysis"""

    def __init__(self, num_iterations=1000, random_seed=None):
        self.num_iterations = num_iterations
        if random_seed is not None:
            np.random.seed(random_seed)

        self.results: List[IterationResult] = []
        print(f"\n{'='*70}")
        print(f"MONTE CARLO PARKING SIMULATION")
        print(f"{'='*70}")
        print(f"Total Capacity: {TOTAL_CAPACITY}")
        print(f"  - Motorcycles: {TOTAL_MC_CAPACITY}")
        print(f"  - Cars: {TOTAL_CAR_CAPACITY}")
        print(f"  - Trucks: {TOTAL_TRUCK_CAPACITY}")
        print(f"Number of Iterations: {num_iterations}")
        print(f"{'='*70}\n")

    def generate_vehicle_type(self):
        """Generate vehicle type based on probability distribution"""
        rand = np.random.random()
        if rand < PROB_MOTORCYCLE:
            return 'motorcycle'
        elif rand < PROB_MOTORCYCLE + PROB_CAR:
            return 'car'
        else:
            return 'truck'

    def generate_arrivals_poisson(self, hour, time_step_minutes=1.0):
        """
        Generate number of arrivals using Poisson distribution
        Formula: P(A=k) = (λ^k * e^(-λ)) / k!

        λ = arrival rate per time step
        """
        hourly_rate = HOURLY_ARRIVAL_RATES.get(hour, 5)
        # Convert hourly rate to rate per time step
        lambda_rate = hourly_rate * (time_step_minutes / 60.0)

        # Sample from Poisson distribution
        num_arrivals = np.random.poisson(lambda_rate)

        # Check for batch arrival during peak hours
        if hour in PEAK_HOURS and np.random.random() < PROB_BATCH_ARRIVAL:
            batch_size = np.random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX + 1)
            num_arrivals += batch_size

        return num_arrivals

    def generate_parking_duration(self, current_time):
        """
        Generate parking duration (vehicle exits between 3:00-6:30 PM)
        current_time in seconds from start of day
        """
        current_hour = current_time / 3600.0

        # Target exit time (uniform random between 15.0 and 18.5)
        target_exit = np.random.uniform(EXIT_TIME_MIN, EXIT_TIME_MAX)

        # Duration in seconds
        duration = max(0.5 * 3600, (target_exit - current_hour) * 3600)
        return duration

    def can_park(self, vehicle_type, state: SimulationState):
        """Check if vehicle can park given current state"""
        if vehicle_type == 'motorcycle':
            return state.mc_occupied < TOTAL_MC_CAPACITY
        elif vehicle_type == 'car':
            return state.car_occupied < TOTAL_CAR_CAPACITY
        elif vehicle_type == 'truck':
            return state.truck_occupied < TOTAL_TRUCK_CAPACITY
        return False

    def park_vehicle(self, vehicle: Vehicle, state: SimulationState):
        """Park vehicle and update state"""
        if vehicle.type == 'motorcycle' and state.mc_occupied < TOTAL_MC_CAPACITY:
            state.mc_occupied += 1
            vehicle.parked = True
            vehicle.parking_zone_type = 'motorcycle'
            return True
        elif vehicle.type == 'car' and state.car_occupied < TOTAL_CAR_CAPACITY:
            state.car_occupied += 1
            vehicle.parked = True
            vehicle.parking_zone_type = 'car'
            return True
        elif vehicle.type == 'truck' and state.truck_occupied < TOTAL_TRUCK_CAPACITY:
            state.truck_occupied += 1
            vehicle.parked = True
            vehicle.parking_zone_type = 'truck'
            return True
        return False

    def remove_vehicle(self, vehicle: Vehicle, state: SimulationState):
        """Remove vehicle from parking and update state"""
        if vehicle.parking_zone_type == 'motorcycle':
            state.mc_occupied = max(0, state.mc_occupied - 1)
        elif vehicle.parking_zone_type == 'car':
            state.car_occupied = max(0, state.car_occupied - 1)
        elif vehicle.parking_zone_type == 'truck':
            state.truck_occupied = max(0, state.truck_occupied - 1)

    def run_single_iteration(self, iteration_num):
        """Run a single simulation iteration (one day)"""
        result = IterationResult(iteration=iteration_num)

        # Current state
        state = SimulationState(time=START_HOUR * 3600)

        # List of all vehicles for this iteration
        vehicles: List[Vehicle] = []
        vehicle_id_counter = 0

        # Time series data collection
        next_collection_time = START_HOUR * 3600

        # Simulate from START_HOUR to END_HOUR
        current_time = START_HOUR * 3600  # Start at 6 AM
        end_time = END_HOUR * 3600  # End at 7 PM

        while current_time < end_time:
            current_hour = int(current_time // 3600)

            # Generate arrivals using Poisson distribution
            if START_HOUR <= current_hour < 17:  # Only spawn vehicles during operating hours
                time_step_minutes = SIMULATION_TIME_STEP / 60.0
                num_arrivals = self.generate_arrivals_poisson(current_hour, time_step_minutes)

                # Create vehicles
                for _ in range(num_arrivals):
                    vehicle_type = self.generate_vehicle_type()
                    duration = self.generate_parking_duration(current_time)

                    vehicle = Vehicle(
                        id=vehicle_id_counter,
                        type=vehicle_type,
                        arrival_time=current_time,
                        departure_time=current_time + duration
                    )
                    vehicle_id_counter += 1
                    result.arrivals += 1

                    # Track by type
                    if vehicle_type == 'motorcycle':
                        result.mc_arrivals += 1
                    elif vehicle_type == 'car':
                        result.car_arrivals += 1
                    elif vehicle_type == 'truck':
                        result.truck_arrivals += 1

                    # Try to park
                    if self.can_park(vehicle_type, state):
                        if self.park_vehicle(vehicle, state):
                            result.parked += 1
                            vehicles.append(vehicle)
                    else:
                        # Vehicle rejected
                        vehicle.rejected = True
                        result.rejected += 1

                        if vehicle_type == 'motorcycle':
                            result.mc_rejected += 1
                        elif vehicle_type == 'car':
                            result.car_rejected += 1
                        elif vehicle_type == 'truck':
                            result.truck_rejected += 1

            # Process departures
            vehicles_to_remove = []
            for vehicle in vehicles:
                if vehicle.parked and current_time >= vehicle.departure_time:
                    self.remove_vehicle(vehicle, state)
                    vehicles_to_remove.append(vehicle)

            for v in vehicles_to_remove:
                vehicles.remove(v)

            # Data collection at intervals
            if current_time >= next_collection_time:
                # Record current state
                state_snapshot = SimulationState(
                    time=current_time,
                    mc_occupied=state.mc_occupied,
                    car_occupied=state.car_occupied,
                    truck_occupied=state.truck_occupied
                )
                result.time_series.append(state_snapshot)

                # Check if full
                if state_snapshot.is_full():
                    result.times_full += 1

                # Track peak
                if state.total_occupied > result.peak_occupancy:
                    result.peak_occupancy = state.total_occupied
                    result.peak_utilization = state.utilization_percent

                next_collection_time += DATA_COLLECTION_INTERVAL

            # Advance time
            current_time += SIMULATION_TIME_STEP

        return result

    def run(self):
        """Run all Monte Carlo iterations"""
        print(f"Running {self.num_iterations} iterations...")

        for i in range(self.num_iterations):
            result = self.run_single_iteration(i)
            self.results.append(result)

            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"  Completed {i + 1}/{self.num_iterations} iterations...")

        print(f"\nAll {self.num_iterations} iterations completed!\n")

    def calculate_statistics(self):
        """Calculate statistical measures across all iterations"""
        arrivals = [r.arrivals for r in self.results]
        parked = [r.parked for r in self.results]
        rejected = [r.rejected for r in self.results]
        peak_occupancy = [r.peak_occupancy for r in self.results]
        peak_utilization = [r.peak_utilization for r in self.results]
        times_full = [r.times_full for r in self.results]

        # Calculate P(Full) - Equation 4 from manuscript
        total_observations = sum(len(r.time_series) for r in self.results)
        total_full_observations = sum(r.times_full for r in self.results)
        prob_full = total_full_observations / total_observations if total_observations > 0 else 0

        stats = {
            'iterations': self.num_iterations,
            'total_capacity': TOTAL_CAPACITY,
            'mc_capacity': TOTAL_MC_CAPACITY,
            'car_capacity': TOTAL_CAR_CAPACITY,
            'truck_capacity': TOTAL_TRUCK_CAPACITY,

            # Arrivals
            'arrivals_mean': np.mean(arrivals),
            'arrivals_std': np.std(arrivals),
            'arrivals_min': np.min(arrivals),
            'arrivals_max': np.max(arrivals),
            'arrivals_ci_95': (np.percentile(arrivals, 2.5), np.percentile(arrivals, 97.5)),

            # Parked
            'parked_mean': np.mean(parked),
            'parked_std': np.std(parked),
            'parked_min': np.min(parked),
            'parked_max': np.max(parked),
            'parked_ci_95': (np.percentile(parked, 2.5), np.percentile(parked, 97.5)),

            # Rejected
            'rejected_mean': np.mean(rejected),
            'rejected_std': np.std(rejected),
            'rejected_min': np.min(rejected),
            'rejected_max': np.max(rejected),
            'rejected_ci_95': (np.percentile(rejected, 2.5), np.percentile(rejected, 97.5)),

            # Peak occupancy
            'peak_occupancy_mean': np.mean(peak_occupancy),
            'peak_occupancy_std': np.std(peak_occupancy),
            'peak_occupancy_min': np.min(peak_occupancy),
            'peak_occupancy_max': np.max(peak_occupancy),

            # Peak utilization
            'peak_utilization_mean': np.mean(peak_utilization),
            'peak_utilization_std': np.std(peak_utilization),

            # Probability of full capacity (Equation 4)
            'probability_full': prob_full,
            'times_full_mean': np.mean(times_full),
        }

        return stats

    def export_results(self, output_dir='monte_carlo_results'):
        """Export results to CSV files"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1. Summary statistics
        stats = self.calculate_statistics()

        stats_df = pd.DataFrame([stats])
        stats_file = os.path.join(output_dir, f'summary_statistics_{timestamp}.csv')
        stats_df.to_csv(stats_file, index=False)
        print(f"[OK] Summary statistics saved to: {stats_file}")

        # 2. Iteration-level results
        iteration_data = []
        for r in self.results:
            iteration_data.append({
                'iteration': r.iteration,
                'arrivals': r.arrivals,
                'parked': r.parked,
                'rejected': r.rejected,
                'peak_occupancy': r.peak_occupancy,
                'peak_utilization': r.peak_utilization,
                'times_full': r.times_full,
                'mc_arrivals': r.mc_arrivals,
                'car_arrivals': r.car_arrivals,
                'truck_arrivals': r.truck_arrivals,
                'mc_rejected': r.mc_rejected,
                'car_rejected': r.car_rejected,
                'truck_rejected': r.truck_rejected,
            })

        iterations_df = pd.DataFrame(iteration_data)
        iterations_file = os.path.join(output_dir, f'iteration_results_{timestamp}.csv')
        iterations_df.to_csv(iterations_file, index=False)
        print(f"[OK] Iteration results saved to: {iterations_file}")

        # 3. Time series data (aggregate across all iterations)
        time_series_data = []
        for result in self.results:
            for state in result.time_series:
                hour = state.time / 3600.0
                time_series_data.append({
                    'iteration': result.iteration,
                    'hour': hour,
                    'time_str': f"{int(hour):02d}:{int((hour % 1) * 60):02d}",
                    'total_occupied': state.total_occupied,
                    'utilization_percent': state.utilization_percent,
                    'mc_occupied': state.mc_occupied,
                    'car_occupied': state.car_occupied,
                    'truck_occupied': state.truck_occupied,
                    'mc_utilization': state.mc_utilization,
                    'car_utilization': state.car_utilization,
                    'truck_utilization': state.truck_utilization,
                    'is_full': state.is_full(),
                })

        time_series_df = pd.DataFrame(time_series_data)
        time_series_file = os.path.join(output_dir, f'time_series_{timestamp}.csv')
        time_series_df.to_csv(time_series_file, index=False)
        print(f"[OK] Time series data saved to: {time_series_file}")

        # 4. Aggregated time series (mean by hour)
        if len(time_series_df) > 0:
            hourly_avg = time_series_df.groupby('time_str').agg({
                'total_occupied': ['mean', 'std', 'min', 'max'],
                'utilization_percent': ['mean', 'std'],
                'mc_occupied': ['mean', 'std'],
                'car_occupied': ['mean', 'std'],
                'truck_occupied': ['mean', 'std'],
                'is_full': 'mean',  # Probability of being full at this time
            }).reset_index()

            hourly_avg.columns = ['_'.join(col).strip('_') for col in hourly_avg.columns.values]
            hourly_file = os.path.join(output_dir, f'hourly_averages_{timestamp}.csv')
            hourly_avg.to_csv(hourly_file, index=False)
            print(f"[OK] Hourly averages saved to: {hourly_file}")

        # 5. Save configuration
        config = {
            'timestamp': timestamp,
            'iterations': self.num_iterations,
            'total_capacity': TOTAL_CAPACITY,
            'mc_capacity': TOTAL_MC_CAPACITY,
            'car_capacity': TOTAL_CAR_CAPACITY,
            'truck_capacity': TOTAL_TRUCK_CAPACITY,
            'hourly_arrival_rates': HOURLY_ARRIVAL_RATES,
            'vehicle_distribution': {
                'motorcycle': PROB_MOTORCYCLE,
                'car': PROB_CAR,
                'truck': PROB_TRUCK
            },
            'peak_hours': PEAK_HOURS,
            'simulation_parameters': {
                'start_hour': START_HOUR,
                'end_hour': END_HOUR,
                'time_step_seconds': SIMULATION_TIME_STEP,
                'data_collection_interval_seconds': DATA_COLLECTION_INTERVAL,
                'max_search_attempts': MAX_SEARCH_ATTEMPTS,
                'circling_timeout_seconds': CIRCLING_TIMEOUT,
            }
        }

        config_file = os.path.join(output_dir, f'config_{timestamp}.json')
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[OK] Configuration saved to: {config_file}")

        return output_dir, timestamp

    def print_summary(self):
        """Print summary of results"""
        stats = self.calculate_statistics()

        print(f"\n{'='*70}")
        print(f"MONTE CARLO SIMULATION RESULTS SUMMARY")
        print(f"{'='*70}\n")

        print(f"Number of Iterations: {stats['iterations']}")
        print(f"Total Capacity: {stats['total_capacity']} (MC:{stats['mc_capacity']}, C:{stats['car_capacity']}, T:{stats['truck_capacity']})")
        print()

        print(f"ARRIVALS:")
        print(f"  Mean:   {stats['arrivals_mean']:.2f} ± {stats['arrivals_std']:.2f}")
        print(f"  Range:  [{stats['arrivals_min']}, {stats['arrivals_max']}]")
        print(f"  95% CI: [{stats['arrivals_ci_95'][0]:.2f}, {stats['arrivals_ci_95'][1]:.2f}]")
        print()

        print(f"PARKED SUCCESSFULLY:")
        print(f"  Mean:   {stats['parked_mean']:.2f} ± {stats['parked_std']:.2f}")
        print(f"  Range:  [{stats['parked_min']}, {stats['parked_max']}]")
        print(f"  95% CI: [{stats['parked_ci_95'][0]:.2f}, {stats['parked_ci_95'][1]:.2f}]")
        print()

        print(f"REJECTED:")
        print(f"  Mean:   {stats['rejected_mean']:.2f} ± {stats['rejected_std']:.2f}")
        print(f"  Range:  [{stats['rejected_min']}, {stats['rejected_max']}]")
        print(f"  95% CI: [{stats['rejected_ci_95'][0]:.2f}, {stats['rejected_ci_95'][1]:.2f}]")
        print()

        print(f"PEAK OCCUPANCY:")
        print(f"  Mean: {stats['peak_occupancy_mean']:.2f} ± {stats['peak_occupancy_std']:.2f}")
        print(f"  Range: [{stats['peak_occupancy_min']}, {stats['peak_occupancy_max']}]")
        print()

        print(f"PEAK UTILIZATION:")
        print(f"  Mean: {stats['peak_utilization_mean']:.2f}% ± {stats['peak_utilization_std']:.2f}%")
        print()

        print(f"PROBABILITY OF FULL CAPACITY (Equation 4):")
        print(f"  P(Full) = {stats['probability_full']:.4f} ({stats['probability_full']*100:.2f}%)")
        print(f"  Average times full per day: {stats['times_full_mean']:.2f}")
        print()

        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description='Monte Carlo Parking Simulation')
    parser.add_argument('--iterations', type=int, default=1000,
                       help='Number of Monte Carlo iterations (default: 1000)')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed for reproducibility (default: None)')
    parser.add_argument('--output-dir', type=str, default='monte_carlo_results',
                       help='Output directory for results (default: monte_carlo_results)')

    args = parser.parse_args()

    # Create and run simulation
    sim = MonteCarloSimulation(num_iterations=args.iterations, random_seed=args.seed)
    sim.run()

    # Print summary
    sim.print_summary()

    # Export results
    output_dir, timestamp = sim.export_results(args.output_dir)

    print(f"\n[SUCCESS] Monte Carlo simulation completed successfully!")
    print(f"Results saved to: {output_dir}/")
    print(f"Use these CSV files for your manuscript analysis and figures.")


if __name__ == '__main__':
    main()
