"""
CNSC CUSTOM MAP PARKING SIMULATION - CLEAN VERSION
===================================================
- Speed options: 1x, 1.5x, 2x, 2.5x, 3x
- Time and vehicle movement synchronized
- Collision avoidance for moving vehicles
- Uses your custom map from generated_parking_zones.py
"""

import pygame
import random
import math
import tkinter as tk
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

# Import layout from generated file
from generated_parking_zones import PARKING_ZONES, BUILDINGS, ROADS, ENTRY_GATE, EXIT_GATE

# Window settings
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60

# Time settings
START_TIME_HOUR = 6
END_TIME_HOUR = 19
BASE_TIME_MULTIPLIER = 60  # Base: 1 real second = 60 sim seconds

# Speed options: 1x, 1.5x, 2x, 2.5x, 3x (multiplier on top of base)
SPEED_OPTIONS = [1.0, 1.5, 2.0, 2.5, 3.0]
DEFAULT_SPEED_INDEX = 0  # Start at 1x

# Colors
GRASS_GREEN = (144, 238, 144)
ROAD_GRAY = (60, 60, 60)
BUILDING_BLUE = (70, 130, 180)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (255, 0, 0)

# Vehicle colors
CAR_COLOR = (30, 144, 255)
MOTORCYCLE_COLOR = (255, 69, 0)
TRUCK_COLOR = (34, 139, 34)

# Calculate capacities
TOTAL_MC_CAPACITY = sum(z["capacity"] for z in PARKING_ZONES if z["zone_type"] == "motorcycle")
TOTAL_CAR_CAPACITY = sum(z["capacity"] for z in PARKING_ZONES if z["zone_type"] == "car")
TOTAL_TRUCK_CAPACITY = sum(z["capacity"] for z in PARKING_ZONES if z["zone_type"] == "truck")
TOTAL_CAPACITY = TOTAL_MC_CAPACITY + TOTAL_CAR_CAPACITY + TOTAL_TRUCK_CAPACITY

# Arrival rates
HOURLY_ARRIVAL_RATES = {
    6: 15, 7: 100, 8: 40, 9: 25, 10: 15, 11: 10,
    12: 60, 13: 30, 14: 15, 15: 8, 16: 5, 17: 2,
}

# Vehicle distribution
PROB_MOTORCYCLE = 0.76
PROB_CAR = 0.20

PROB_BATCH_ARRIVAL = 0.40
BATCH_SIZE_MIN = 2
BATCH_SIZE_MAX = 6
MAX_SEARCH_ATTEMPTS = 4


class VehicleState(Enum):
    ENTERING = 1
    ON_ROAD = 2
    PARKED = 3
    EXITING = 4
    CIRCLING = 5


@dataclass
class Waypoint:
    x: float
    y: float


@dataclass
class Vehicle:
    id: int
    type: str
    arrival_time: float
    departure_time: float
    state: VehicleState = VehicleState.ENTERING
    zone_index: int = -1
    x: float = 0
    y: float = 0
    color: Tuple[int, int, int] = None
    rejected: bool = False
    path: List[Waypoint] = None
    current_waypoint: int = 0
    base_speed: float = 2.5  # Base movement speed
    parking_slot: Tuple[int, int] = None
    search_attempts: int = 0
    circling_time: float = 0

    def __post_init__(self):
        if self.color is None:
            if self.type == 'car':
                self.color = CAR_COLOR
            elif self.type == 'truck':
                self.color = TRUCK_COLOR
            else:
                self.color = MOTORCYCLE_COLOR
        if self.path is None:
            self.path = []


class ParkingZone:
    def __init__(self, name, x, y, width, height, capacity, zone_type):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.capacity = int(capacity)
        self.type = zone_type
        self.occupied = 0
        self.parked_vehicles = []

        self.padding = 2
        self.gap = 1

        usable_width = width - (self.padding * 2)
        usable_height = height - (self.padding * 2)

        best_cols = 1
        best_rows = self.capacity
        best_score = -999999

        for cols in range(1, self.capacity + 1):
            rows = math.ceil(self.capacity / cols)
            slot_w = (usable_width - (cols - 1) * self.gap) / cols
            slot_h = (usable_height - (rows - 1) * self.gap) / rows

            if slot_w > 0 and slot_h > 0:
                ratio = slot_w / slot_h
                ideal_ratio = 1.5 if zone_type != 'motorcycle' else 1.2
                ratio_score = -abs(ratio - ideal_ratio) * 10
                area_score = min(slot_w, slot_h)
                if ratio > 4 or ratio < 0.25:
                    ratio_score -= 100
                total_score = ratio_score + area_score
                if total_score > best_score:
                    best_cols = cols
                    best_rows = rows
                    best_score = total_score

        self.slots_per_row = best_cols
        self.num_rows = best_rows
        self.slot_width = (usable_width - (self.slots_per_row - 1) * self.gap) / self.slots_per_row
        self.slot_height = (usable_height - (self.num_rows - 1) * self.gap) / self.num_rows
        self.slots = {}
        self._init_slots()

    def _init_slots(self):
        row = col = 0
        for i in range(self.capacity):
            self.slots[(row, col)] = None
            col += 1
            if col >= self.slots_per_row:
                col = 0
                row += 1

    def find_empty_slot(self):
        for pos, vehicle in self.slots.items():
            if vehicle is None:
                return pos
        return None

    def get_slot_position(self, slot):
        row, col = slot
        x = self.x + self.padding + col * (self.slot_width + self.gap) + self.slot_width / 2
        y = self.y + self.padding + row * (self.slot_height + self.gap) + self.slot_height / 2
        return (int(x), int(y))

    def can_park(self, vehicle_type):
        return self.type == vehicle_type and self.occupied < self.capacity

    def park_vehicle(self, vehicle):
        if self.can_park(vehicle.type):
            slot = self.find_empty_slot()
            if slot:
                self.slots[slot] = vehicle
                vehicle.parking_slot = slot
                self.occupied += 1
                self.parked_vehicles.append(vehicle)
                return True
        return False

    def remove_vehicle(self, vehicle):
        if vehicle in self.parked_vehicles:
            if vehicle.parking_slot:
                self.slots[vehicle.parking_slot] = None
            self.parked_vehicles.remove(vehicle)
            self.occupied -= 1

    def get_utilization(self):
        return (self.occupied / self.capacity * 100) if self.capacity > 0 else 0


class RoadNetwork:
    def __init__(self, roads):
        self.roads = roads
        self.road_rects = []
        self.road_centers = []

        for road in roads:
            rect = pygame.Rect(road["x"], road["y"], road["width"], road["height"])
            self.road_rects.append(rect)
            cx = road["x"] + road["width"] // 2
            cy = road["y"] + road["height"] // 2
            is_horizontal = road["width"] > road["height"]
            self.road_centers.append({
                'rect': rect,
                'cx': cx, 'cy': cy,
                'x': road["x"], 'y': road["y"],
                'w': road["width"], 'h': road["height"],
                'horizontal': is_horizontal
            })

    def get_nearest_road_point(self, x, y):
        min_dist = float('inf')
        nearest = (x, y)
        nearest_road = None

        for road in self.road_centers:
            rx, ry = road['x'], road['y']
            rw, rh = road['w'], road['h']
            cx = max(rx, min(x, rx + rw))
            cy = max(ry, min(y, ry + rh))
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = (cx, cy)
                nearest_road = road

        return nearest, nearest_road

    def find_intersections(self, road1, road2):
        r1 = road1['rect']
        r2 = road2['rect']
        if r1.colliderect(r2):
            ix = max(r1.left, r2.left) + (min(r1.right, r2.right) - max(r1.left, r2.left)) // 2
            iy = max(r1.top, r2.top) + (min(r1.bottom, r2.bottom) - max(r1.top, r2.top)) // 2
            return (ix, iy)
        return None

    def create_road_path(self, start, end):
        path = [Waypoint(start[0], start[1])]
        road_start_pt, road_start = self.get_nearest_road_point(start[0], start[1])
        road_end_pt, road_end = self.get_nearest_road_point(end[0], end[1])

        if road_start is None or road_end is None:
            path.append(Waypoint(end[0], end[1]))
            return path

        path.append(Waypoint(road_start_pt[0], road_start_pt[1]))

        if road_start == road_end:
            path.append(Waypoint(road_end_pt[0], road_end_pt[1]))
        else:
            intersection = self.find_intersections(road_start, road_end)
            if intersection:
                path.append(Waypoint(intersection[0], intersection[1]))
                path.append(Waypoint(road_end_pt[0], road_end_pt[1]))
            else:
                for mid_road in self.road_centers:
                    if mid_road == road_start or mid_road == road_end:
                        continue
                    int1 = self.find_intersections(road_start, mid_road)
                    int2 = self.find_intersections(mid_road, road_end)
                    if int1 and int2:
                        path.append(Waypoint(int1[0], int1[1]))
                        path.append(Waypoint(int2[0], int2[1]))
                        path.append(Waypoint(road_end_pt[0], road_end_pt[1]))
                        break
                else:
                    if road_start['horizontal']:
                        path.append(Waypoint(road_end_pt[0], road_start_pt[1]))
                    else:
                        path.append(Waypoint(road_start_pt[0], road_end_pt[1]))
                    path.append(Waypoint(road_end_pt[0], road_end_pt[1]))

        path.append(Waypoint(end[0], end[1]))
        return path


class StatsWindow:
    def __init__(self, simulation):
        self.sim = simulation
        self.root = tk.Tk()
        self.root.title("Simulation Controls")
        self.root.geometry("350x450+50+50")
        self.root.resizable(False, False)
        self.root.configure(bg='#2b2b2b')
        self.root.attributes('-topmost', True)
        self.setup_ui()
        self.running = True

    def setup_ui(self):
        title = tk.Label(self.root, text="SIMULATION STATS", font=('Arial', 16, 'bold'),
                        fg='white', bg='#2b2b2b')
        title.pack(pady=10)

        time_frame = tk.Frame(self.root, bg='#3d5a80', relief='ridge', bd=2)
        time_frame.pack(fill='x', padx=10, pady=5)

        self.day_label = tk.Label(time_frame, text="Day 1", font=('Arial', 14, 'bold'),
                                  fg='white', bg='#3d5a80')
        self.day_label.pack(pady=5)

        self.time_label = tk.Label(time_frame, text="06:00 AM", font=('Arial', 24, 'bold'),
                                   fg='yellow', bg='#3d5a80')
        self.time_label.pack(pady=5)

        self.peak_label = tk.Label(time_frame, text="", font=('Arial', 10),
                                   fg='red', bg='#3d5a80')
        self.peak_label.pack(pady=2)

        stats_frame = tk.LabelFrame(self.root, text="Statistics", font=('Arial', 11, 'bold'),
                                    fg='white', bg='#2b2b2b')
        stats_frame.pack(fill='x', padx=10, pady=10)

        self.capacity_label = tk.Label(stats_frame, text=f"Capacity: {TOTAL_CAPACITY}",
                                       font=('Arial', 10), fg='lightgray', bg='#2b2b2b')
        self.capacity_label.pack(anchor='w', padx=10, pady=2)

        self.arrivals_label = tk.Label(stats_frame, text="Arrivals: 0", font=('Arial', 11),
                                       fg='lightgreen', bg='#2b2b2b')
        self.arrivals_label.pack(anchor='w', padx=10, pady=2)

        self.parked_label = tk.Label(stats_frame, text="Parked: 0", font=('Arial', 11),
                                     fg='cyan', bg='#2b2b2b')
        self.parked_label.pack(anchor='w', padx=10, pady=2)

        self.inside_label = tk.Label(stats_frame, text="Currently Inside: 0", font=('Arial', 11),
                                     fg='yellow', bg='#2b2b2b')
        self.inside_label.pack(anchor='w', padx=10, pady=2)

        self.rejected_label = tk.Label(stats_frame, text="Rejected: 0", font=('Arial', 11),
                                       fg='red', bg='#2b2b2b')
        self.rejected_label.pack(anchor='w', padx=10, pady=2)

        speed_frame = tk.LabelFrame(self.root, text="Speed Control", font=('Arial', 11, 'bold'),
                                    fg='white', bg='#2b2b2b')
        speed_frame.pack(fill='x', padx=10, pady=10)

        speed_row = tk.Frame(speed_frame, bg='#2b2b2b')
        speed_row.pack(pady=10)

        self.btn_slower = tk.Button(speed_row, text=" - ", font=('Arial', 16, 'bold'),
                                    bg='#c44', fg='white', width=4, command=self.speed_down)
        self.btn_slower.pack(side='left', padx=10)

        self.speed_label = tk.Label(speed_row, text="1x", font=('Arial', 18, 'bold'),
                                    fg='yellow', bg='#2b2b2b', width=6)
        self.speed_label.pack(side='left', padx=10)

        self.btn_faster = tk.Button(speed_row, text=" + ", font=('Arial', 16, 'bold'),
                                    bg='#4c4', fg='white', width=4, command=self.speed_up)
        self.btn_faster.pack(side='left', padx=10)

        ctrl_frame = tk.Frame(self.root, bg='#2b2b2b')
        ctrl_frame.pack(fill='x', padx=10, pady=10)

        self.btn_pause = tk.Button(ctrl_frame, text="PAUSE", font=('Arial', 12, 'bold'),
                                   bg='#666', fg='white', width=12, command=self.toggle_pause)
        self.btn_pause.pack(side='left', padx=10)

        self.btn_reset = tk.Button(ctrl_frame, text="RESET", font=('Arial', 12, 'bold'),
                                   bg='#844', fg='white', width=12, command=self.reset_sim)
        self.btn_reset.pack(side='left', padx=10)

    def speed_up(self):
        if self.sim.speed_index < len(SPEED_OPTIONS) - 1:
            self.sim.speed_index += 1
            self.sim.speed = SPEED_OPTIONS[self.sim.speed_index]

    def speed_down(self):
        if self.sim.speed_index > 0:
            self.sim.speed_index -= 1
            self.sim.speed = SPEED_OPTIONS[self.sim.speed_index]

    def toggle_pause(self):
        self.sim.paused = not self.sim.paused

    def reset_sim(self):
        self.sim.reset()

    def update(self):
        if not self.running:
            return

        self.day_label.config(text=f"Day {self.sim.current_day}")
        self.time_label.config(text=self.sim.get_current_time_string())

        if self.sim.is_peak_hour():
            self.peak_label.config(text="PEAK HOUR", fg='red')
        else:
            self.peak_label.config(text="")

        self.arrivals_label.config(text=f"Arrivals: {self.sim.total_arrivals}")
        self.parked_label.config(text=f"Parked: {self.sim.total_parked}")
        self.inside_label.config(text=f"Currently Inside: {len(self.sim.vehicles)}")
        self.rejected_label.config(text=f"Rejected: {self.sim.total_rejected}")

        speed_text = f"{self.sim.speed:.1f}x" if self.sim.speed % 1 != 0 else f"{int(self.sim.speed)}x"
        self.speed_label.config(text=speed_text)

        if self.sim.paused:
            self.btn_pause.config(text="RESUME", bg='#a84')
        else:
            self.btn_pause.config(text="PAUSE", bg='#666')

        self.root.after(100, self.update)

    def close(self):
        self.running = False
        try:
            self.root.destroy()
        except:
            pass


class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("CNSC Parking Simulation")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 16)

        self.zones = [ParkingZone(**zone) for zone in PARKING_ZONES]
        self.road_network = RoadNetwork(ROADS)

        self.sim_time = START_TIME_HOUR * 3600
        self.speed_index = DEFAULT_SPEED_INDEX
        self.speed = SPEED_OPTIONS[self.speed_index]
        self.current_day = 1

        self.vehicles = []
        self.vehicle_counter = 0
        self.total_arrivals = 0
        self.total_parked = 0
        self.total_rejected = 0
        self.total_departed = 0
        self.paused = False

        # Auto-calculate zoom
        max_x = max(
            max((z["x"] + z["width"]) for z in PARKING_ZONES),
            max((b[1] + b[3]) for b in BUILDINGS),
            max((r["x"] + r["width"]) for r in ROADS)
        )
        max_y = max(
            max((z["y"] + z["height"]) for z in PARKING_ZONES),
            max((b[2] + b[4]) for b in BUILDINGS),
            max((r["y"] + r["height"]) for r in ROADS)
        )
        zoom_x = (WINDOW_WIDTH - 40) / max_x
        zoom_y = (WINDOW_HEIGHT - 40) / max_y
        self.zoom = min(zoom_x, zoom_y) * 0.95
        self.view_offset_x = 15
        self.view_offset_y = 15

    def get_current_hour(self):
        return int(self.sim_time // 3600) % 24

    def get_current_time_string(self):
        total_seconds = int(self.sim_time)
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        period = "AM" if hours < 12 else "PM"
        display_hour = hours if hours <= 12 else hours - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour:02d}:{minutes:02d} {period}"

    def is_peak_hour(self):
        hour = self.get_current_hour()
        return hour in [7, 8, 12, 13]

    def get_arrival_rate(self):
        hour = self.get_current_hour()
        return HOURLY_ARRIVAL_RATES.get(hour, 5)

    def get_parking_duration(self):
        current_hour = self.get_current_hour()
        minutes = (int(self.sim_time) % 3600) // 60
        current_time = current_hour + (minutes / 60.0)
        target_exit = random.uniform(15.0, 18.5)
        duration = max(0.5, target_exit - current_time)
        return duration * 3600

    def spawn_vehicle(self):
        rand = random.random()
        if rand < PROB_MOTORCYCLE:
            vehicle_type = 'motorcycle'
        elif rand < PROB_MOTORCYCLE + PROB_CAR:
            vehicle_type = 'car'
        else:
            vehicle_type = 'truck'

        duration = self.get_parking_duration()
        vehicle = Vehicle(
            id=self.vehicle_counter,
            type=vehicle_type,
            arrival_time=self.sim_time,
            departure_time=self.sim_time + duration,
            x=ENTRY_GATE[0],
            y=ENTRY_GATE[1],
            state=VehicleState.ENTERING
        )
        self.vehicle_counter += 1
        self.total_arrivals += 1
        self.vehicles.append(vehicle)
        self.assign_parking(vehicle)

    def assign_parking(self, vehicle):
        available_zones = [(i, zone) for i, zone in enumerate(self.zones)
                          if zone.can_park(vehicle.type)]

        if not available_zones:
            vehicle.search_attempts += 1
            if vehicle.search_attempts >= MAX_SEARCH_ATTEMPTS:
                vehicle.rejected = True
                vehicle.state = VehicleState.EXITING
                vehicle.path = self.road_network.create_road_path(
                    (vehicle.x, vehicle.y), EXIT_GATE)
                vehicle.current_waypoint = 0
                self.total_rejected += 1
            else:
                vehicle.state = VehicleState.CIRCLING
                vehicle.circling_time = self.sim_time
            return

        zone_index, zone = random.choice(available_zones)
        if zone.park_vehicle(vehicle):
            vehicle.zone_index = zone_index
            slot_pos = zone.get_slot_position(vehicle.parking_slot)
            vehicle.path = self.road_network.create_road_path(
                (vehicle.x, vehicle.y), slot_pos)
            vehicle.current_waypoint = 0

            # Only count as "parked" if this is first time getting a slot (not circling retry)
            was_circling = vehicle.state == VehicleState.CIRCLING
            vehicle.state = VehicleState.ON_ROAD

            if not was_circling:
                self.total_parked += 1

    def check_collision(self, vehicle, new_x, new_y):
        """Check collision with other moving vehicles only"""
        min_distance = 12
        for other in self.vehicles:
            if other.id == vehicle.id or other.state == VehicleState.PARKED:
                continue
            dist = math.sqrt((new_x - other.x)**2 + (new_y - other.y)**2)
            if dist < min_distance:
                return True
        return False

    def update(self, dt):
        if self.paused:
            return

        # Time increases: base multiplier × speed
        # At 1x: 1 real sec = 60 sim secs
        # At 2x: 1 real sec = 120 sim secs (2x faster)
        self.sim_time += dt * BASE_TIME_MULTIPLIER * self.speed

        # Day transition
        if self.sim_time >= 19 * 3600:
            parked_count = sum(1 for v in self.vehicles if v.state == VehicleState.PARKED)
            if parked_count == 0:
                self.sim_time = START_TIME_HOUR * 3600
                self.current_day += 1
                self.vehicles = []

        # Spawn vehicles (scaled with speed to match time progression)
        current_hour = self.get_current_hour()
        if 6 <= current_hour < 17:
            arrival_rate = self.get_arrival_rate()
            # Scale spawn rate with simulation speed
            spawn_prob = arrival_rate * dt * self.speed / 60.0
            if random.random() < spawn_prob:
                if random.random() < PROB_BATCH_ARRIVAL and self.is_peak_hour():
                    for _ in range(random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)):
                        self.spawn_vehicle()
                else:
                    self.spawn_vehicle()

        vehicles_to_remove = []

        for vehicle in self.vehicles:
            # Departure check
            if vehicle.state == VehicleState.PARKED and self.sim_time >= vehicle.departure_time:
                zone = self.zones[vehicle.zone_index]
                zone.remove_vehicle(vehicle)
                vehicle.state = VehicleState.EXITING
                vehicle.path = self.road_network.create_road_path(
                    (vehicle.x, vehicle.y), EXIT_GATE)
                vehicle.current_waypoint = 0
                self.total_departed += 1

            # Circling timeout
            if vehicle.state == VehicleState.CIRCLING:
                if self.sim_time - vehicle.circling_time > 300:
                    vehicle.rejected = True
                    vehicle.state = VehicleState.EXITING
                    vehicle.path = self.road_network.create_road_path(
                        (vehicle.x, vehicle.y), EXIT_GATE)
                    vehicle.current_waypoint = 0
                    self.total_rejected += 1
                elif random.random() < 0.03:
                    self.assign_parking(vehicle)

            # Movement (synchronized with speed)
            if vehicle.state in [VehicleState.ENTERING, VehicleState.ON_ROAD, VehicleState.EXITING]:
                # Use movement budget to handle multiple waypoints per frame at high speeds
                movement_budget = vehicle.base_speed * self.speed
                iterations = 0
                max_iterations = 50  # Safety limit

                while movement_budget > 0.1 and vehicle.current_waypoint < len(vehicle.path) and iterations < max_iterations:
                    iterations += 1
                    wp = vehicle.path[vehicle.current_waypoint]
                    dx = wp.x - vehicle.x
                    dy = wp.y - vehicle.y
                    dist = math.sqrt(dx**2 + dy**2)

                    if dist > 1:
                        # Move towards waypoint, but not more than remaining budget
                        step = min(movement_budget, dist)
                        new_x = vehicle.x + (dx / dist) * step
                        new_y = vehicle.y + (dy / dist) * step

                        # Check collision before moving
                        if not self.check_collision(vehicle, new_x, new_y):
                            vehicle.x = new_x
                            vehicle.y = new_y
                            movement_budget -= step
                        else:
                            # Blocked, stop moving
                            break
                    else:
                        # Close enough to waypoint, move to next
                        vehicle.current_waypoint += 1

                # Check if path complete
                if vehicle.current_waypoint >= len(vehicle.path):
                    if vehicle.state in [VehicleState.ENTERING, VehicleState.ON_ROAD]:
                        vehicle.state = VehicleState.PARKED
                    elif vehicle.state == VehicleState.EXITING:
                        vehicles_to_remove.append(vehicle)

            elif vehicle.state == VehicleState.CIRCLING:
                vehicle.x += random.uniform(-2, 2)
                vehicle.y += random.uniform(-2, 2)

        for v in vehicles_to_remove:
            self.vehicles.remove(v)

    def world_to_screen(self, x, y):
        sx = (x + self.view_offset_x) * self.zoom
        sy = (y + self.view_offset_y) * self.zoom
        return int(sx), int(sy)

    def draw(self):
        self.screen.fill(GRASS_GREEN)

        # Draw roads
        for road in ROADS:
            x, y = self.world_to_screen(road["x"], road["y"])
            w = int(road["width"] * self.zoom)
            h = int(road["height"] * self.zoom)
            pygame.draw.rect(self.screen, ROAD_GRAY, (x, y, w, h))

        # Draw parking zones
        for zone in self.zones:
            x, y = self.world_to_screen(zone.x, zone.y)
            w = int(zone.width * self.zoom)
            h = int(zone.height * self.zoom)

            if zone.type == "motorcycle":
                color = (255, 253, 208)
            elif zone.type == "car":
                color = (221, 160, 221)
            else:
                color = (255, 182, 193)

            util = zone.get_utilization()
            if util >= 100:
                color = tuple(max(0, c - 50) for c in color)

            pygame.draw.rect(self.screen, color, (x, y, w, h))
            pygame.draw.rect(self.screen, BLACK, (x, y, w, h), 2)

            label = self.font_small.render(f"{zone.name} {zone.occupied}/{zone.capacity}", True, BLACK)
            self.screen.blit(label, (x + 2, y + 2))

        # Draw buildings
        for bldg in BUILDINGS:
            name, bx, by, bw, bh = bldg
            x, y = self.world_to_screen(bx, by)
            w = int(bw * self.zoom)
            h = int(bh * self.zoom)
            pygame.draw.rect(self.screen, BUILDING_BLUE, (x, y, w, h))
            pygame.draw.rect(self.screen, BLACK, (x, y, w, h), 1)
            if w > 40 and h > 20:
                label = self.font_small.render(name, True, WHITE)
                self.screen.blit(label, (x + 2, y + 2))

        # Draw vehicles
        for vehicle in self.vehicles:
            x, y = self.world_to_screen(vehicle.x, vehicle.y)
            if vehicle.zone_index >= 0 and vehicle.state == VehicleState.PARKED:
                zone = self.zones[vehicle.zone_index]
                vw = int(zone.slot_width * 0.95 * self.zoom)
                vh = int(zone.slot_height * 0.95 * self.zoom)
                size = (max(vw, 4), max(vh, 3))
            else:
                if vehicle.type == 'truck':
                    size = (int(35 * self.zoom), int(20 * self.zoom))
                elif vehicle.type == 'car':
                    size = (int(24 * self.zoom), int(14 * self.zoom))
                else:
                    size = (int(14 * self.zoom), int(8 * self.zoom))
                size = (max(size[0], 6), max(size[1], 4))

            rect = pygame.Rect(x - size[0]//2, y - size[1]//2, size[0], size[1])
            pygame.draw.rect(self.screen, vehicle.color, rect, border_radius=1)
            pygame.draw.rect(self.screen, BLACK, rect, 1, border_radius=1)

        # Draw gates
        ex, ey = self.world_to_screen(ENTRY_GATE[0], ENTRY_GATE[1])
        size = int(15 * self.zoom)
        pygame.draw.circle(self.screen, GREEN, (ex, ey), size)
        pygame.draw.circle(self.screen, BLACK, (ex, ey), size, 2)

        ex, ey = self.world_to_screen(EXIT_GATE[0], EXIT_GATE[1])
        pygame.draw.circle(self.screen, RED, (ex, ey), size)
        pygame.draw.circle(self.screen, BLACK, (ex, ey), size, 2)

        hint = self.font_small.render("SPACE=Pause  UP/DOWN=Speed  R=Reset  ESC=Exit", True, WHITE)
        pygame.draw.rect(self.screen, (30, 30, 40), (5, WINDOW_HEIGHT - 25, hint.get_width() + 10, 22))
        self.screen.blit(hint, (10, WINDOW_HEIGHT - 22))

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_UP:
                    if self.speed_index < len(SPEED_OPTIONS) - 1:
                        self.speed_index += 1
                        self.speed = SPEED_OPTIONS[self.speed_index]
                elif event.key == pygame.K_DOWN:
                    if self.speed_index > 0:
                        self.speed_index -= 1
                        self.speed = SPEED_OPTIONS[self.speed_index]
                elif event.key == pygame.K_r:
                    self.reset()
        return True

    def reset(self):
        self.sim_time = START_TIME_HOUR * 3600
        self.current_day = 1
        self.speed_index = DEFAULT_SPEED_INDEX
        self.speed = SPEED_OPTIONS[self.speed_index]
        self.vehicles = []
        self.vehicle_counter = 0
        self.total_arrivals = 0
        self.total_parked = 0
        self.total_rejected = 0
        self.total_departed = 0
        for zone in self.zones:
            zone.occupied = 0
            zone.parked_vehicles = []
            zone._init_slots()

    def run(self, stats_window):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()

            try:
                stats_window.root.update()
            except tk.TclError:
                running = False

        stats_window.close()
        pygame.quit()


if __name__ == "__main__":
    print("=" * 70)
    print("CNSC PARKING SIMULATION - CLEAN VERSION")
    print("=" * 70)
    print(f"\nCapacity: {TOTAL_CAPACITY} total")
    print(f"  - Motorcycles: {TOTAL_MC_CAPACITY}")
    print(f"  - Cars: {TOTAL_CAR_CAPACITY}")
    print(f"  - Trucks: {TOTAL_TRUCK_CAPACITY}")
    print(f"\nSpeed options: 1x, 1.5x, 2x, 2.5x, 3x")
    print(f"Collision avoidance: Enabled")
    print("=" * 70)

    sim = Simulation()
    stats_win = StatsWindow(sim)
    stats_win.update()
    sim.run(stats_win)
