#!/usr/bin/env python3
# coding=utf-8

from controller import Supervisor
import random

class CrazylFlie():
    HEIGHT = 0.3
    TRAJECTORY_POINTS = 50
    TAKE_OFF_POINTS = 10
    X_Y_VAR = 1
    ARENA_SIZE = 2.4

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

        if random.random() > 0.5:
            new_x_position = x_position + random.uniform(-self.X_Y_VAR, self.X_Y_VAR)
            new_x_position = max(-self.ARENA_SIZE, min(self.ARENA_SIZE, new_x_position))
            new_y_position = y_position
        else:
            new_y_position = y_position + random.uniform(-self.X_Y_VAR, self.X_Y_VAR)
            new_y_position = max(-self.ARENA_SIZE, min(self.ARENA_SIZE, new_y_position))
            new_x_position = x_position

        dx = (new_x_position - x_position) / self.TRAJECTORY_POINTS
        dy = (new_y_position - y_position) / self.TRAJECTORY_POINTS

        x_positions = [x_position + (dx * it) for it in range(self.TRAJECTORY_POINTS)]
        y_positions = [y_position + (dy * it) for it in range(self.TRAJECTORY_POINTS)]
        z_position = self.HEIGHT

        return x_positions, y_positions, z_position

    def run(self):
        last_position = self.cf_translation_field.getSFVec3f()
        count = 0

        while self.cf_supervisor.step(32) != -1:
            self.rotateMotors(count)
            if not count % self.TRAJECTORY_POINTS:
                x_trajectory, y_trajectory, z_position = self.genNewPoint()

            self.markTrajectory(last_position)
            current_position = [
                x_trajectory[count % self.TRAJECTORY_POINTS],
                y_trajectory[count % self.TRAJECTORY_POINTS],
                z_position
            ]
            self.cf_translation_field.setSFVec3f(current_position)

            last_position = current_position
            count += 1

if __name__ == '__main__':
    cf = CrazylFlie()
    cf.run()