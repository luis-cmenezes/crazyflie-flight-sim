#!/usr/bin/env python3
#coding=utf-8

from controller import Supervisor, Motor
import random

HEIGHT = 0.3
TRAJECTORY_POINTS = 100
TAKE_OFF_POINTS = 100
X_Y_VAR = 1
ARENA_SIZE = 2.4

class CrazylFlie():

    #Realiza a captura dos "nodes" necessários para alterar a simulação 
    #e configura os nodes estáticos
    def __init__(self):
        
        self.cf_supervisor = Supervisor()

        cf_node = self.cf_supervisor.getFromDef('Crazyflie')

        #Campos que serão manipulados para reprodução do voo
        self.cf_translation_field = cf_node.getField('translation')
        self.cf_rotation_field = cf_node.getField('rotation')

        #Motores, utilizados apenas para efeito estético
        m1 = self.cf_supervisor.getFromDef('M1_MOTOR')
        self.m1_rotation = m1.getField('rotation')

        m2 = self.cf_supervisor.getFromDef('M2_MOTOR')
        self.m2_rotation = m2.getField('rotation')
        
        m3 = self.cf_supervisor.getFromDef('M3_MOTOR')
        self.m3_rotation = m3.getField('rotation')

        m4 = self.cf_supervisor.getFromDef('M4_MOTOR')
        self.m4_rotation = m4.getField('rotation')
        
    def rotateMotors(self, count):
        new_cw_rotation = self.m1_rotation.getSFRotation()[:3]+[count*0.52]
        new_ccw_rotation = self.m2_rotation.getSFRotation()[:3]+[-count*0.52]

        self.m1_rotation.setSFRotation(new_cw_rotation)
        self.m2_rotation.setSFRotation(new_ccw_rotation)
        self.m3_rotation.setSFRotation(new_cw_rotation)
        self.m4_rotation.setSFRotation(new_ccw_rotation)
    
    def takeOff(self):
        x_position, y_position, z_position = self.cf_translation_field.getSFVec3f()

        new_z_position = HEIGHT

        z_positions = [0]*TAKE_OFF_POINTS
        dz = (new_z_position-z_position)/TAKE_OFF_POINTS

        for it in range(TAKE_OFF_POINTS):
            z_positions[it] = z_position + (dz*it)
            self.cf_translation_field.setSFVec3f([x_position, y_position, z_positions[it]])
            self.cf_supervisor.step(32)

    def genNewPoint(self):
        x_position, y_position, z_position = self.cf_translation_field.getSFVec3f()

        new_x_position = x_position+random.uniform(-X_Y_VAR,X_Y_VAR)
        new_x_position = max(-ARENA_SIZE,new_x_position)
        new_x_position = min(ARENA_SIZE,new_x_position)
        new_y_position = y_position+random.uniform(-X_Y_VAR,X_Y_VAR)
        new_y_position = max(-ARENA_SIZE,new_y_position)
        new_y_position = min(ARENA_SIZE,new_y_position)
        
        x_positions = [0]*TRAJECTORY_POINTS
        y_positions = [0]*TRAJECTORY_POINTS
        dx = (new_x_position-x_position)/TRAJECTORY_POINTS
        dy = (new_y_position-y_position)/TRAJECTORY_POINTS

        for it in range(TRAJECTORY_POINTS):
            x_positions[it] = x_position + (dx*it)
            y_positions[it] = y_position + (dy*it)

        return x_positions, y_positions, z_position

    def run(self):
        self.takeOff()

        last_position = self.cf_translation_field.getSFVec3f()
        count = 0.0
        
        while self.cf_supervisor.step(32) != -1:
            self.rotateMotors(count)
            if not count%TRAJECTORY_POINTS:
                x_trajectory, y_trajectory, z_position = self.genNewPoint()
            
            current_position = [x_trajectory[int(count%TRAJECTORY_POINTS)],y_trajectory[int(count%TRAJECTORY_POINTS)],z_position]
            self.cf_translation_field.setSFVec3f(current_position)

            last_position = current_position
            count += 1.0

if __name__ == '__main__':
    cf = CrazylFlie()

    cf.run()