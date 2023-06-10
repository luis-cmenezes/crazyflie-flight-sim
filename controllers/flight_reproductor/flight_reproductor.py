#!/usr/bin/env python3
# coding=utf-8

from controller import Supervisor
import random

class CrazylFlie():
    MIN_HEIGHT = 0.3
    MAX_HEIGHT = 1
    TRAJECTORY_POINTS = 100
    X_Y_VAR = 0.5
    Z_VAR = 0.1
    ARENA_SIZE = 0.8

    def __init__(self):
        self.cf_supervisor = Supervisor()
        cf_node = self.cf_supervisor.getFromDef('Crazyflie')

        self.cf_translation_field = cf_node.getField('translation')
        self.cf_rotation_field = cf_node.getField('rotation')

        motor_nodes = [self.cf_supervisor.getFromDef(f'M{m}_MOTOR') for m in range(1, 5)]
        self.motor_rotations = [motor.getField('rotation') for motor in motor_nodes]

        coords_node = self.cf_supervisor.getFromDef('TRAJECTORY_COORDINATES')
        self.coords_field = coords_node.getField('point')

    def markTrajectory(self, coord):
        self.coords_field.insertMFVec3f(-1, coord)

    def rotateMotors(self, count):
        rotation_value = count * 1.52
        for index, rotation in enumerate(self.motor_rotations):
            new_rotation = rotation.getSFRotation()[:3] + [rotation_value if index%2 else -rotation_value]
            rotation.setSFRotation(new_rotation)

    def genNewPoint(self):
        x_position, y_position, z_position = self.cf_translation_field.getSFVec3f()

        movement = random.random()
        if movement < 1/3:
            new_x_position = x_position + random.uniform(-self.X_Y_VAR, self.X_Y_VAR)
            new_x_position = max(-self.ARENA_SIZE, min(self.ARENA_SIZE, new_x_position))
            new_y_position = y_position
            new_z_position = max(z_position, self.MIN_HEIGHT)
        elif movement < 2/3:
            new_y_position = y_position + random.uniform(-self.X_Y_VAR, self.X_Y_VAR)
            new_y_position = max(-self.ARENA_SIZE, min(self.ARENA_SIZE, new_y_position))
            new_x_position = x_position
            new_z_position = max(z_position, self.MIN_HEIGHT)
        else:
            new_z_position = z_position + random.uniform(-self.Z_VAR, self.Z_VAR)
            new_z_position = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, new_z_position))
            new_x_position = x_position
            new_y_position = y_position

        dx = (new_x_position - x_position) / self.TRAJECTORY_POINTS
        dy = (new_y_position - y_position) / self.TRAJECTORY_POINTS
        dz = (new_z_position - z_position) / self.TRAJECTORY_POINTS

        x_positions = [x_position + (dx * it) for it in range(self.TRAJECTORY_POINTS)]
        y_positions = [y_position + (dy * it) for it in range(self.TRAJECTORY_POINTS)]
        z_positions = [z_position + (dz * it) for it in range(self.TRAJECTORY_POINTS)]

        return x_positions, y_positions, z_positions

    def run(self):
        last_position = self.cf_translation_field.getSFVec3f()
        count = 0

        while self.cf_supervisor.step(32) != -1:
            self.rotateMotors(count)
            if not count % self.TRAJECTORY_POINTS:
                x_trajectory, y_trajectory, z_trajectory = self.genNewPoint()

            self.markTrajectory(last_position)
            current_position = [
                x_trajectory[count % self.TRAJECTORY_POINTS],
                y_trajectory[count % self.TRAJECTORY_POINTS],
                z_trajectory[count % self.TRAJECTORY_POINTS]
            ]
            self.cf_translation_field.setSFVec3f(current_position)

            last_position = current_position
            count += 1

if __name__ == '__main__':
    cf = CrazylFlie()
    cf.run()