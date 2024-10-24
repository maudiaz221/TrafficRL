import pygame
import numpy as np
import random
from enum import Enum

# Initialize Pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)

class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

class Vehicle:
    def __init__(self, position, direction):
        self.position = list(position)  # [x, y] for easier updating
        self.direction = direction
        self.waiting_time = 0
        self.has_crossed = False
        self.speed = 2  # pixels per frame
        self.size = 20  # size of vehicle in pixels
        
    def draw(self, screen):
        color = BLUE if self.waiting_time == 0 else YELLOW
        pygame.draw.rect(screen, color, 
                        (self.position[0] - self.size//2,
                         self.position[1] - self.size//2,
                         self.size, self.size))

class TrafficLight:
    def __init__(self, position):
        self.position = position
        self.is_green = False
        self.timer = 0
        self.cycle_duration = 150  # frames
        self.size = 20
        
    def draw(self, screen):
        color = GREEN if self.is_green else RED
        pygame.draw.circle(screen, color, 
                         (self.position[0], self.position[1]), 
                         self.size//2)
    
    def update(self):
        self.timer += 1
        if self.timer >= self.cycle_duration:
            self.is_green = not self.is_green
            self.timer = 0

class TrafficEnvironment:
    def __init__(self, width=800, height=600, traffic_density='medium'):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Traffic Simulation")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Road properties
        self.road_width = 60
        self.vehicles = []
        self.traffic_density = traffic_density
        
        # Calculate center lines of roads
        self.vertical_center = width // 2
        self.horizontal_center = height // 2
        
        # Initialize traffic lights
        self.traffic_lights = {
            'north': TrafficLight((self.vertical_center, self.horizontal_center - self.road_width//2)),
            'south': TrafficLight((self.vertical_center, self.horizontal_center + self.road_width//2)),
            'east': TrafficLight((self.vertical_center + self.road_width//2, self.horizontal_center)),
            'west': TrafficLight((self.vertical_center - self.road_width//2, self.horizontal_center))
        }
        
        # Set opposite traffic lights to same state
        self.traffic_lights['north'].is_green = True
        self.traffic_lights['south'].is_green = True
        self.traffic_lights['east'].is_green = False
        self.traffic_lights['west'].is_green = False
        
    def add_vehicle(self):
        """Add vehicles based on traffic density"""
        if self.traffic_density == 'low':
            spawn_probability = 0.02
        elif self.traffic_density == 'medium':
            spawn_probability = 0.04
        else:  # high
            spawn_probability = 0.08
            
        if random.random() < spawn_probability:
            # Define spawn points and directions
            spawn_points = [
                ((self.vertical_center, self.height), Direction.NORTH),
                ((self.vertical_center, 0), Direction.SOUTH),
                ((0, self.horizontal_center), Direction.EAST),
                ((self.width, self.horizontal_center), Direction.WEST)
            ]
            
            position, direction = random.choice(spawn_points)
            self.vehicles.append(Vehicle(position, direction))
    
    def update_vehicles(self):
        """Update vehicle positions"""
        for vehicle in list(self.vehicles):
            if vehicle.has_crossed:
                self.vehicles.remove(vehicle)
                continue
                
            x, y = vehicle.position
            
            # Check if at intersection
            at_intersection = (
                abs(x - self.vertical_center) < 30 and
                abs(y - self.horizontal_center) < 30
            )
            
            can_move = True
            if at_intersection:
                # Check traffic light
                if vehicle.direction in [Direction.NORTH, Direction.SOUTH]:
                    can_move = self.traffic_lights['north'].is_green
                else:
                    can_move = self.traffic_lights['east'].is_green
                
                if not can_move:
                    vehicle.waiting_time += 1
            
            # Check for vehicles ahead
            for other in self.vehicles:
                if other != vehicle and not other.has_crossed:
                    if self._vehicles_too_close(vehicle, other):
                        can_move = False
                        vehicle.waiting_time += 1
                        break
            
            if can_move:
                # Update position based on direction
                if vehicle.direction == Direction.NORTH:
                    vehicle.position[1] -= vehicle.speed
                elif vehicle.direction == Direction.SOUTH:
                    vehicle.position[1] += vehicle.speed
                elif vehicle.direction == Direction.EAST:
                    vehicle.position[0] += vehicle.speed
                else:  # WEST
                    vehicle.position[0] -= vehicle.speed
                
                # Check if vehicle has left the screen
                if (vehicle.position[0] < 0 or vehicle.position[0] > self.width or
                    vehicle.position[1] < 0 or vehicle.position[1] > self.height):
                    vehicle.has_crossed = True
    
    def _vehicles_too_close(self, v1, v2):
        """Check if two vehicles are too close"""
        min_distance = 30  # minimum safe distance
        x1, y1 = v1.position
        x2, y2 = v2.position
        
        if v1.direction == v2.direction:
            if v1.direction in [Direction.NORTH, Direction.SOUTH]:
                return abs(x1 - x2) < v1.size and abs(y1 - y2) < min_distance
            else:
                return abs(y1 - y2) < v1.size and abs(x1 - x2) < min_distance
        return False
    
    def draw(self):
        """Draw the environment"""
        # Fill background
        self.screen.fill(WHITE)
        
        # Draw roads
        pygame.draw.rect(self.screen, GRAY, 
                        (self.vertical_center - self.road_width//2, 0,
                         self.road_width, self.height))
        pygame.draw.rect(self.screen, GRAY,
                        (0, self.horizontal_center - self.road_width//2,
                         self.width, self.road_width))
        
        # Draw road lines
        line_color = (255, 255, 0)  # Yellow
        # Vertical road lines
        pygame.draw.line(self.screen, line_color,
                        (self.vertical_center, 0),
                        (self.vertical_center, self.height), 2)
        # Horizontal road lines
        pygame.draw.line(self.screen, line_color,
                        (0, self.horizontal_center),
                        (self.width, self.horizontal_center), 2)
        
        # Draw traffic lights
        for light in self.traffic_lights.values():
            light.draw(self.screen)
        
        # Draw vehicles
        for vehicle in self.vehicles:
            vehicle.draw(self.screen)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.traffic_density = 'low'
                    elif event.key == pygame.K_2:
                        self.traffic_density = 'medium'
                    elif event.key == pygame.K_3:
                        self.traffic_density = 'high'
            
            # Update traffic lights
            for light in self.traffic_lights.values():
                light.update()
            
            # Ensure opposite traffic lights are synchronized
            self.traffic_lights['south'].is_green = self.traffic_lights['north'].is_green
            self.traffic_lights['west'].is_green = self.traffic_lights['east'].is_green
            
            # Add new vehicles
            self.add_vehicle()
            
            # Update vehicle positions
            self.update_vehicles()
            
            # Draw everything
            self.draw()
            
            # Control frame rate
            self.clock.tick(60)
        
        pygame.quit()

def main():
    env = TrafficEnvironment(traffic_density='medium')
    env.run()

if __name__ == "__main__":
    main()