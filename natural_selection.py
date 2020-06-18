import numpy as np
import math

from time import strftime, gmtime

from raylib.pyray import PyRay
from raylib.colors import *

pyray = PyRay()

MIN_RANDOM_SPEED = 0.05
MAX_RANDOM_SPEED = 0.15

MIN_RANDOM_SIZE = 1
MAX_RANDOM_SIZE = 2

MIN_RANDOM_SIGHT = 15
MAX_RANDOM_SIGHT = 25

MUTATION_CHANCE = 0.05

START_ENERGY = 100
FOOD_ENERGY = 50
MATE_ENERGY = 100

SPEED_FACTOR = 1.0
SIZE_FACTOR = 1.0
SIGHT_FACTOR = 0.01

CREATURE_COLOR = RED
FOOD_COLOR = BLUE

class Creature:
    def __init__(self, raylib, world, x, y, speed, size, sight, energy = START_ENERGY):
        # Set raylib
        self.raylib = raylib
        
        # Set world
        self.world = world

        # Set position
        self.position = np.array([x, size/2, y])

        # Set direction randomly
        self.direction = np.random.rand() * 2 * np.pi

        # Set is_dead
        self.is_dead = False
        
        # Set mate
        self.mate = None
        
        # Set children
        self.children = []

        # Set traits
        self.speed = speed
        self.size = size
        self.sight = sight
        
        # Set energy
        self.energy = energy
        self.deltaEnergy = 1/2 * (size * SIZE_FACTOR) ** 3 * (speed * SPEED_FACTOR) ** 2 + sight * SIGHT_FACTOR

    def step(self):
        # Loose Energy
        self.energy -= self.deltaEnergy

        # Find closest food
        closest_food = sorted(self.world.food, key=self.distance_to)[0]
        distance_to_food = self.distance_to(closest_food)

        # Find closest creature
        closest_creature = sorted(self.world.creatures, key=self.distance_to)[1]
        distance_to_creature = self.distance_to(closest_creature)

        target = None
        self.mate = None

        if distance_to_food <= self.sight or distance_to_creature <= self.sight:
            if distance_to_food > distance_to_creature and self.energy > MATE_ENERGY:
                target = closest_creature
                self.mate = closest_creature
            else:
                target = closest_food

        if distance_to_food <= self.size/2:
            self.energy += FOOD_ENERGY
            closest_food.is_eaten = True

        # Check for target
        if target != None:
            vec_to_target = target.position - self.position
            self.direction = math.atan2(vec_to_target[0], vec_to_target[2])
        else:
            # Set new random direction
            self.direction += np.pi / 16 * np.random.randn()

        velocity = self.speed * np.array([np.sin(self.direction), 0.0, np.cos(self.direction)])

        # Move to new position
        self.position += velocity
        self.position = np.clip(self.position, -self.world.size/2, self.world.size/2)

        # Die if energy is 0
        if self.energy <= 0:
            self.is_dead = True
            return

        # self.raylib.draw_circle_3d(list(self.position), self.sight, [1.0, 0.0, 0.0], 90, CREATURE_COLOR)
        self.raylib.draw_cube(list(self.position), self.size, self.size, self.size, CREATURE_COLOR)

    def distance_to(self, obj_with_pos):
        return math.sqrt(sum(x**2 for x in obj_with_pos.position - self.position))

    def get_child(self, mutation_chance):
        parents = [self, self.mate]

        # Set childs position to parents position
        child_x = parents[0].position[0]
        child_y = parents[0].position[2]

        # Select speed randomly and mutate
        speed = np.random.choice(parents).speed
        if np.random.random() < mutation_chance:
            speed += np.random.random() * (MAX_RANDOM_SPEED - MIN_RANDOM_SPEED) + MIN_RANDOM_SPEED

        # Select size randomly and mutate
        size = np.random.choice(parents).size
        if np.random.random() < mutation_chance:
            size += np.random.random() * (MAX_RANDOM_SIZE - MIN_RANDOM_SIZE) + MIN_RANDOM_SIZE

        # Select sight randomly and mutate
        sight = np.random.choice(parents).sight
        if np.random.random() < mutation_chance:
            sight += np.random.random() * (MAX_RANDOM_SIGHT - MIN_RANDOM_SIGHT) + MIN_RANDOM_SIGHT

        # Init child creature
        child = Creature(
            parents[0].raylib,
            parents[0].world,
            child_x,
            child_y,
            speed,
            size,
            sight,
            MATE_ENERGY
        )

        # Add child to parents children
        for parent in parents:
            parent.energy -= MATE_ENERGY/2
            parent.children.append(child)

        return child

class Food:
    def __init__(self, raylib, x, y):
        # Set raylib
        self.raylib = raylib

        # Set position
        self.position = np.array([x, 0.25, y])

        # Set is_eaten
        self.is_eaten = False

    def draw(self):
        self.raylib.draw_sphere(list(self.position), 0.5, FOOD_COLOR)

class World:
    def __init__(self, raylib, size, creature_count, food_count):
        # Set raylib
        self.raylib = raylib

        # Set size
        self.size = size

        # Generate creatures
        self.creatures = []
        for i in range(creature_count):
            self.creatures.append(Creature(
                raylib,
                self,
                np.random.random() * size - size/2,
                np.random.random() * size - size/2,
                np.random.random() * (MAX_RANDOM_SPEED - MIN_RANDOM_SPEED) + MIN_RANDOM_SPEED,
                np.random.random() * (MAX_RANDOM_SIZE - MIN_RANDOM_SIZE) + MIN_RANDOM_SIZE,
                np.random.random() * (MAX_RANDOM_SIGHT - MIN_RANDOM_SIGHT) + MIN_RANDOM_SIGHT
            ))

        # Generate food
        self.food = []
        for i in range(food_count):
            self.food.append(Food(
                raylib,
                np.random.random() * size - size/2,
                np.random.random() * size - size/2
            ))

        self.snapshots = "snapshots_" +  strftime("%a_%d-%b-%Y_%H:%M:%S", gmtime()) + ".npz"
        np.savez_compressed(self.snapshots, np.array([]))

    def update_and_draw(self):
        print("Population Size: ", len(self.creatures))

        # Draw plane
        self.raylib.draw_plane([0.0, -0.5, 0.0], [self.size, self.size], DARKGRAY)

        snapshot = []

        # Each creature takes one step
        # Draw each creature and remove if dead
        for creature in self.creatures:
            creature.step()

            snapshot.append({"speed": creature.speed, "size": creature.size, "sight": creature.sight, "children_count": len(creature.children), "has_mate": creature.mate != None})

            # Get child
            if creature.mate != None and creature.distance_to(creature.mate) < (creature.size + creature.mate.size)/2:
                    self.creatures.append(creature.get_child(MUTATION_CHANCE))

            if creature.is_dead:
                self.creatures.remove(creature)

        snapshots = []
        data = np.load(self.snapshots, allow_pickle=True)
        for e in data:
            snapshots.append(data[e])
        snapshots.append(snapshot)

        np.savez_compressed(self.snapshots, *snapshots)

        # Draw each piece of food and remove and create new if eaten
        for piece in self.food:
            piece.draw()

            if piece.is_eaten:
                self.food.remove(piece)
                self.food.append(Food(
                    self.raylib,
                    np.random.random() * self.size - self.size/2,
                    np.random.random() * self.size - self.size/2
                ))

world = World(pyray, 100, 20, 40)

pyray.init_window(800, 600, "Natural Selection")
pyray.set_target_fps(60)

# TODO: fix weird display bug

camera = pyray.Camera3D([100.0, 100.0, 100.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0], 45.0, 0)
pyray.set_camera_mode(camera, pyray.CAMERA_PERSPECTIVE)

while not pyray.window_should_close():
    pyray.update_camera(pyray.pointer(camera))
    pyray.begin_drawing()
    pyray.clear_background(RAYWHITE)
    pyray.begin_mode_3d(camera)
    world.update_and_draw()
    pyray.end_mode_3d()
    pyray.draw_fps(10, 10)
    pyray.end_drawing()
pyray.close_window()

