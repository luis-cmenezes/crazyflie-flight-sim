#!/usr/bin/env python3
# coding=utf-8

import sys
from controller import Supervisor
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
import math

class CrazylFlie(QWidget):

    def __init__(self):
        self.fileSelector()
        self.getDataFromFile()
        self.initSimUtilities()

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
                rotation_data = rotation_data.split(',')
                
                #Transformando strings em numérico
                sensor_data = [float(sensor)/1000 for sensor in sensor_data] #Divisão por 1000 para mm->m
                position_data = [float(position) for position in position_data] 
                rotation_data = [float(rotation) for rotation in rotation_data]
                
                #Salvando dados para utilização posterior
                self.sensorReads.append(sensor_data)
                self.positions.append(position_data)
                self.rotations.append(rotation_data)

        #Checagens de segurança do algoritmo
        assert len(self.sensorReads) == len(self.positions)
        assert len(self.sensorReads) == len(self.rotations)
        assert len(self.sensorReads[0]) == 4
        assert len(self.positions[0]) == 3
        assert len(self.rotations[0]) == 3

    def initSimUtilities(self):
        self.cf_supervisor = Supervisor()
        cf_node = self.cf_supervisor.getFromDef('Crazyflie')

        self.cf_translation_field = cf_node.getField('translation')
        self.cf_rotation_field = cf_node.getField('rotation')

        motor_nodes = [self.cf_supervisor.getFromDef(f'M{m}_MOTOR') for m in range(1, 5)]
        self.motor_rotations = [motor.getField('rotation') for motor in motor_nodes]

        coords_node = self.cf_supervisor.getFromDef('TRAJECTORY_COORDINATES')
        self.coords_field = coords_node.getField('point')

    def run(self):
        last_position = self.cf_translation_field.getSFVec3f()
        count = 0

        while self.cf_supervisor.step(32) != -1 and count < len(self.positions):
            self.rotateMotors(count)
            
            [current_position, current_rotation] = self.getNewPoint(count)
            current_rotation = self.rpy2xyza(current_rotation)

            self.cf_translation_field.setSFVec3f(current_position)
            self.cf_rotation_field.setSFRotation(current_rotation)

            self.markTrajectory(last_position)            

            last_position = current_position

            count += 1

    def rpy2xyza(self, rpy_dg):
        # Converter os ângulos de graus para radianos
        roll_rad = math.radians(rpy_dg[0])
        pitch_rad = math.radians(rpy_dg[1])
        yaw_rad = math.radians(rpy_dg[2])

        # Calcular os componentes do vetor de eixos
        x = math.cos(roll_rad) * math.sin(pitch_rad) * math.sin(yaw_rad) + \
            math.sin(roll_rad) * math.cos(pitch_rad) * math.cos(yaw_rad)
        y = math.sin(roll_rad) * math.cos(pitch_rad) * math.sin(yaw_rad) - \
            math.cos(roll_rad) * math.sin(pitch_rad) * math.cos(yaw_rad)
        z = math.cos(roll_rad) * math.cos(pitch_rad) * math.sin(yaw_rad) - \
            math.sin(roll_rad) * math.sin(pitch_rad) * math.cos(yaw_rad)

        # Calcular o ângulo de rotação
        angle = 2 * math.acos(math.sqrt(x**2 + y**2 + z**2))

        # Retornar o vetor de eixos e o ângulo
        return [x, y, z, angle]

    def markTrajectory(self, coord):
        self.coords_field.insertMFVec3f(-1, coord)

    def rotateMotors(self, count):
        rotation_value = count * 1.52
        for index, rotation in enumerate(self.motor_rotations):
            new_rotation = rotation.getSFRotation()[:3] + [rotation_value if index%2 else -rotation_value]
            rotation.setSFRotation(new_rotation)

    def getNewPoint(self, count):
        
        return self.positions[count], self.rotations[count]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    cf = CrazylFlie()
    app.quit()
    cf.run()