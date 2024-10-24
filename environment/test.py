import pygame
import numpy as np
from enum import Enum
import math
import random

# Initialize Pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARK_GRAY = (64, 64, 64)

class GameState(Enum):
    PLACING_BUILDING = 1
    DRAWING_ROAD = 2
    PLACING_TRAFFIC_LIGHT = 3
    SIMULATING = 4

class BuildingType(Enum):
    SOURCE = 1  # Buildings that generate cars
    DESTINATION = 2  # Buildings that receive cars

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = text
        self.font = pygame.font.Font(None, 30)
        self.active = False

    def draw(self, screen):
        color = (*self.color, 200) if self.active else (*self.color, 255)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Building:
    def __init__(self, position, building_type, spawn_rate=1.0):
        self.position = position
        self.type = building_type
        self.spawn_rate = spawn_rate
        self.spawn_timer = 0
        self.size = 40
        self.connections = []  # Road points connected to this building
        self.rect = pygame.Rect(position[0] - self.size//2,
                              position[1] - self.size//2,
                              self.size, self.size)
    
    def draw(self, screen):
        color = BLUE if self.type == BuildingType.SOURCE else GREEN
        pygame.draw.rect(screen, color, self.rect)
        # Draw highlight if building has connections
        if self.connections:
            pygame.draw.rect(screen, YELLOW, self.rect, 2)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Road:
    def __init__(self):
        self.points = []
        self.width = 20
        self.connected_buildings = []  # Keep track of connected buildings
    
    def add_point(self, point):
        self.points.append(point)
    
    def draw(self, screen):
        if len(self.points) < 2:
            return
        
        # Draw road segments
        for i in range(len(self.points) - 1):
            start = self.points[i]
            end = self.points[i + 1]
            pygame.draw.line(screen, GRAY, start, end, self.width)
            
        # Draw connection points
        for point in self.points:
            pygame.draw.circle(screen, DARK_GRAY, point, 5)
            
        # Highlight end points if connected to buildings
        for building in self.connected_buildings:
            closest_point = self.get_closest_point(building.position)
            pygame.draw.circle(screen, YELLOW, closest_point, 8)

    def get_closest_point(self, position):
        closest_point = None
        min_distance = float('inf')
        
        for point in self.points:
            dist = math.hypot(point[0] - position[0], point[1] - position[1])
            if dist < min_distance:
                min_distance = dist
                closest_point = point
                
        return closest_point

class TrafficSimulation:
    def __init__(self, width=1200, height=800):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Traffic Simulation Designer")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game objects
        self.buildings = []
        self.roads = []
        self.traffic_lights = []
        self.cars = []
        
        # Game state
        self.state = GameState.PLACING_BUILDING
        self.current_road = None
        self.selected_building_type = BuildingType.SOURCE
        self.spawn_rate = 1.0
        self.selected_building = None  # For road connections
        
        # Create buttons
        button_y = 10
        button_height = 40
        self.buttons = {
            'source': Button(10, button_y, 150, button_height, "Source Building", (100, 200, 255)),
            'destination': Button(170, button_y, 150, button_height, "Destination", (100, 255, 100)),
            'road': Button(330, button_y, 150, button_height, "Draw Road", (200, 200, 200)),
            'traffic_light': Button(490, button_y, 150, button_height, "Traffic Light", (255, 200, 100)),
            'simulate': Button(650, button_y, 150, button_height, "Simulate", (255, 100, 100))
        }
        self.buttons['source'].active = True
        
    def set_state(self, new_state):
        self.state = new_state
        # Reset all buttons
        for button in self.buttons.values():
            button.active = False
            
        # Activate appropriate button
        if new_state == GameState.PLACING_BUILDING:
            if self.selected_building_type == BuildingType.SOURCE:
                self.buttons['source'].active = True
            else:
                self.buttons['destination'].active = True
        elif new_state == GameState.DRAWING_ROAD:
            self.buttons['road'].active = True
        elif new_state == GameState.PLACING_TRAFFIC_LIGHT:
            self.buttons['traffic_light'].active = True
        elif new_state == GameState.SIMULATING:
            self.buttons['simulate'].active = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check button clicks first
                button_clicked = False
                for name, button in self.buttons.items():
                    if button.is_clicked(mouse_pos):
                        button_clicked = True
                        if name == 'source':
                            self.selected_building_type = BuildingType.SOURCE
                            self.set_state(GameState.PLACING_BUILDING)
                        elif name == 'destination':
                            self.selected_building_type = BuildingType.DESTINATION
                            self.set_state(GameState.PLACING_BUILDING)
                        elif name == 'road':
                            self.set_state(GameState.DRAWING_ROAD)
                            self.current_road = None
                        elif name == 'traffic_light':
                            self.set_state(GameState.PLACING_TRAFFIC_LIGHT)
                        elif name == 'simulate':
                            self.set_state(GameState.SIMULATING)
                
                if button_clicked:
                    continue
                
                # Handle game state actions
                if self.state == GameState.PLACING_BUILDING:
                    if mouse_pos[1] > 60:  # Don't place buildings over UI
                        self.buildings.append(Building(mouse_pos, 
                                                    self.selected_building_type,
                                                    self.spawn_rate))
                
                elif self.state == GameState.DRAWING_ROAD:
                    # Check if clicked on a building
                    clicked_building = None
                    for building in self.buildings:
                        if building.is_clicked(mouse_pos):
                            clicked_building = building
                            break
                    
                    if clicked_building:
                        if not self.current_road:
                            # Start new road from building
                            self.current_road = Road()
                            self.roads.append(self.current_road)
                            self.current_road.add_point(clicked_building.position)
                            self.current_road.connected_buildings.append(clicked_building)
                            clicked_building.connections.append(self.current_road)
                        else:
                            # End road at building
                            self.current_road.add_point(clicked_building.position)
                            self.current_road.connected_buildings.append(clicked_building)
                            clicked_building.connections.append(self.current_road)
                            self.current_road = None
                    else:
                        # Add road point if not clicking building
                        if self.current_road:
                            self.current_road.add_point(mouse_pos)
                
                elif self.state == GameState.PLACING_TRAFFIC_LIGHT:
                    self.traffic_lights.append(TrafficLight(mouse_pos))
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.current_road = None
                elif event.key == pygame.K_UP:
                    self.spawn_rate += 0.1
                elif event.key == pygame.K_DOWN:
                    self.spawn_rate = max(0.1, self.spawn_rate - 0.1)
    
    def draw(self):
        # Fill background
        self.screen.fill(WHITE)
        
        # Draw roads
        for road in self.roads:
            road.draw(self.screen)
        
        # Draw current road being placed
        if self.current_road:
            self.current_road.draw(self.screen)
            # Draw line from last point to mouse
            if self.current_road.points:
                mouse_pos = pygame.mouse.get_pos()
                pygame.draw.line(self.screen, GRAY, 
                               self.current_road.points[-1], 
                               mouse_pos, 
                               self.current_road.width)
        
        # Draw buildings
        for building in self.buildings:
            building.draw(self.screen)
        
        # Draw traffic lights
        for light in self.traffic_lights:
            light.draw(self.screen)
        
        # Draw cars
        for car in self.cars:
            car.draw(self.screen)
        
        # Draw UI
        for button in self.buttons.values():
            button.draw(self.screen)
        
        # Draw spawn rate
        font = pygame.font.Font(None, 36)
        spawn_text = f"Spawn Rate: {self.spawn_rate:.1f}"
        spawn_surface = font.render(spawn_text, True, BLACK)
        self.screen.blit(spawn_surface, (810, 20))
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()

def main():
    sim = TrafficSimulation()
    sim.run()

if __name__ == "__main__":
    main()