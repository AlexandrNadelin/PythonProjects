import logging
import threading
import serial
from PyQt5.QtCore import pyqtSignal, QObject
#from queue import Queue
import time
from Modbus import *
import struct

class VS_04M_comPortConnector(threading.Thread,QObject):
    devNameReceived = pyqtSignal(str)
    devDataReceived = pyqtSignal(float,float,float,float,float,float,float)
    connectionClosed = pyqtSignal()
    sendMessageToGui = pyqtSignal(str)

    def __init__(self):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.portNumber = 0
        self.baudRate=115200
        self.modbusAddress=0x80
        self.isComplate=False
        self.isConnected = False

        self.request =""

    def setNewParameters(self,modbasAddress,baudRate):
        registers = [baudRate&0xFFFF,baudRate>>16,modbasAddress]
        self.request = setHoldingRegistersRequest(self.modbusAddress,2048,registers)

    def setPortNumber(self, portNumber):
        if not isinstance(portNumber, str):
            return
        self.portNumber = portNumber

    def setBaudRate(self, baudRate):
        if not isinstance(baudRate, int):
            return
        self.baudRate = baudRate

    def setModbusAddress(self, modbusAddress):
        if not isinstance(modbusAddress, int):
            return
        self.modbusAddress = modbusAddress

    def connectDevice(self):
        if self.portNumber == 0:
            return
        self.start()

    def closeConnection(self):
        self.isComplate=True
        self.join()

    def run(self):
        self.serialPort = serial.Serial()
        self.serialPort.port=self.portNumber
        self.serialPort.baudrate=self.baudRate  #int(self.comboBoxBaudRate.currentText(),10)
        #self.serialPort.timeout=2.0
        self.serialPort.timeout=1.5

        try: 
            self.serialPort.open()
            line = self.serialPort.readline()  #check is continuous mode enebled
            
            self.serialPort.timeout= 1.5 #0.2
            if  line.__len__()!=0:
                self.serialPort.write(setHoldingRegistersRequest(self.modbusAddress,2048+4,[0x0000,]).encode())  #reset continuous mode
                line = self.serialPort.readline()
            
            
            self.serialPort.write(getInfoRequest(self.modbusAddress).encode())  #(":80116F\r\n".encode())
            line = self.serialPort.readline()
            if line.__len__()==0:
                print("Device not connected")
                self.serialPort.close()
                self.connectionClosed.emit()
                self.sendMessageToGui.emit("Device not connected")
                return

            line = line[1:-2]
            lineBytes = bytearray.fromhex(line.decode())
            if sum(lineBytes)&0xFF!=0:  #crc error
                print("crc error")
                self.serialPort.close()
                self.connectionClosed.emit()
                self.sendMessageToGui.emit("crc error")
                return
            if lineBytes[1]&0x80!=0:  #request error
                print("request error")
                self.serialPort.close()
                self.connectionClosed.emit()
                self.sendMessageToGui.emit("request error")
                return
            lineBytes=lineBytes[3:3+lineBytes[2]-1]
            self.devNameReceived.emit(lineBytes.decode("utf-8"))

            self.serialPort.write(setHoldingRegistersRequest(self.modbusAddress,2048+4,[0x0002,]).encode())  #set continuous mode
            line = self.serialPort.readline()

            self.serialPort.timeout=4.0
            self.isConnected = True
            while self.isComplate==False:
                try:
                    line = self.serialPort.readline()
                    if line.__len__()<9:
                        print("line len = 0")
                        continue
                    line = line[1:-2]
                    lineBytes = bytearray.fromhex(line.decode())
                    if (sum(lineBytes)&0xFF)!=0:  #crc error
                        continue
                    if lineBytes[1]&0x80!=0:  #request error
                        continue
                    devAddr = lineBytes[0]
                    command = lineBytes[1]
                    
                    '''my_struct = struct.Struct("<fffffff")
                    res = my_struct.unpack_from(lineBytes[3:31])
                    self.devDataReceived.emit(*res)'''

                    peakAcceleration = struct.unpack('<f',lineBytes[3:7])
                    rmsAcceleration = struct.unpack('<f',lineBytes[7:11])
                    rmsSpeed = struct.unpack('<f',lineBytes[11:15])
                    peakFactor = struct.unpack('<f',lineBytes[15:19])
                    KurtosisX = struct.unpack('<f',lineBytes[19:23])
                    KurtosisY = struct.unpack('<f',lineBytes[23:27])
                    KurtosisZ = struct.unpack('<f',lineBytes[27:31])
                    self.devDataReceived.emit(peakAcceleration[0],rmsAcceleration[0],rmsSpeed[0],peakFactor[0],KurtosisX[0],KurtosisY[0],KurtosisZ[0])

                    if self.request!="" :
                        self.serialPort.write(self.request.encode())  #set continuous mode
                        line = self.serialPort.readline()
                        self.request=""

                except TimeoutError:
                    print("TimeoutError")
        except Exception as e:
            print("error serial port: "+str(e))
        else:            
            self.serialPort.write(setHoldingRegistersRequest(self.modbusAddress,2048+4,[0x0000,]).encode())  #set continuous mode
            line = self.serialPort.readline()

            self.serialPort.close()
        finally:
            if self.serialPort.isOpen():
                self.serialPort.close()
            self.connectionClosed.emit()
            self.isConnected = False

    