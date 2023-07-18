#!/usr/bin/env python3
# coding=utf-8

import sys
from controller import Supervisor
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
import math

class CrazylFlie(QWidget):

    def __init__(self):
        self.initSimUtilities()
        self.fileSelector()
        self.getDataFromFile()        

    def fileSelector(self):
        super().__init__()
        self.fileName, _ = QFileDialog.getOpenFileName(self,"Escolha o arquivo de dados", "/home","Data Files (*.txt)")

    def getDataFromFile(self):
        self.sensorReads = []
        self.positions = []
        self.rotations = []

        with open(self.fileName, 'r') as file:
            for line in file:
                #Separando cada tipo de dado
                [sensor_data, position_data, rotation_data] = line.strip().split('|')

                #Separando os dados do mesmo tipo. Ex: Position em x,y,z
                sensor_data = sensor_data.split(',')
                position_data = position_data.split(',')
                rotation_data = rotation_data.split(',')[2]
                
                #Transformando strings em numérico
                sensor_data = [float(sensor)/1000 for sensor in sensor_data] #Divisão por 1000 para mm->m
                position_data = [float(position) for position in position_data] 
                rotation_data = math.radians(float(rotation_data))
                
                #Salvando dados para utilização posterior
                self.sensorReads.append(sensor_data)
                self.positions.append(position_data)
                self.rotations.append(rotation_data)

        #Checagens de segurança do algoritmo
        assert len(self.sensorReads) == len(self.positions)
        assert len(self.sensorReads) == len(self.rotations)
        assert len(self.sensorReads[0]) == 4
        assert len(self.positions[0]) == 3
        assert type(self.rotations[0]) == float

    def initSimUtilities(self):
        self.cf_supervisor = Supervisor()
        cf_node = self.cf_supervisor.getFromDef('Crazyflie')

        self.cf_translation_field = cf_node.getField('translation')
        self.cf_rotation_field = cf_node.getField('rotation')

        motor_nodes = [self.cf_supervisor.getFromDef(f'M{m}_MOTOR') for m in range(1, 5)]
        self.motor_rotations = [motor.getField('rotation') for motor in motor_nodes]

        coords_node = self.cf_supervisor.getFromDef('TRAJECTORY_COORDINATES')
        self.coords_field = coords_node.getField('point')

        self.front_sensor_pos = self.cf_supervisor.getFromDef('FRONT_SENSOR').getField('translation')
        self.front_sensor_len = self.cf_supervisor.getFromDef('FRONT_LASER').getField('height')

        self.back_sensor_pos = self.cf_supervisor.getFromDef('BACK_SENSOR').getField('translation')
        self.back_sensor_len = self.cf_supervisor.getFromDef('BACK_LASER').getField('height')

        self.left_sensor_pos = self.cf_supervisor.getFromDef('LEFT_SENSOR').getField('translation')
        self.left_sensor_len = self.cf_supervisor.getFromDef('LEFT_LASER').getField('height')

        self.right_sensor_pos = self.cf_supervisor.getFromDef('RIGHT_SENSOR').getField('translation')
        self.right_sensor_len = self.cf_supervisor.getFromDef('RIGHT_LASER').getField('height')

    def run(self):
        last_position = self.cf_translation_field.getSFVec3f()
        count = 0

        while self.cf_supervisor.step(32) != -1 and count < len(self.positions):
            self.rotateMotors(count)
            
            [current_position, current_rotation, current_measures] = self.getNewPoint(count)

            self.cf_translation_field.setSFVec3f(current_position)
            self.cf_rotation_field.setSFRotation(current_rotation)   
            self.updateSensor(current_measures)         

            self.markTrajectory(last_position)            

            last_position = current_position

            count += 1

    def updateSensor(self, measures):
       self.front_sensor_pos.setSFVec3f([measures[3]/2, 0, 0])
       self.front_sensor_len.setSFFloat(measures[3])

       self.back_sensor_pos.setSFVec3f([-measures[0]/2, 0, 0])
       self.back_sensor_len.setSFFloat(measures[0])

       self.left_sensor_pos.setSFVec3f([0, measures[2]/2, 0])
       self.left_sensor_len.setSFFloat(measures[2])

       self.right_sensor_pos.setSFVec3f([0, -measures[1]/2, 0])
       self.right_sensor_len.setSFFloat(measures[1])

    def markTrajectory(self, coord):
        self.coords_field.insertMFVec3f(-1, coord)

    def rotateMotors(self, count):
        rotation_value = count * 1.52
        for index, rotation in enumerate(self.motor_rotations):
            new_rotation = rotation.getSFRotation()[:3] + [rotation_value if index%2 else -rotation_value]
            rotation.setSFRotation(new_rotation)

    def getNewPoint(self, count):
        
        return self.positions[count], [0, 0, 1, self.rotations[count]], self.sensorReads[count]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    cf = CrazylFlie()
    app.quit()
    cf.run()