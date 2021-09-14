from PyQt5 import QtWidgets
from pyqtgraph.functions import Color
import serial
import glob
from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import (QTextEdit, QWidget, QVBoxLayout, QHBoxLayout,QLabel, QApplication,QLineEdit,QMessageBox,QPushButton,QComboBox,QFileDialog,QDesktopWidget)
from PyQt5.QtGui import QFont
import sys  # We need sys so that we can pass argv to QApplication
import os
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import datetime
from VS_04M_comPortConnector import VS_04M_comPortConnector as connector
#from ThreadSaveQueue import ThreadSaveFixedQueue
#current_dir = os.path.dirname(os.path.abspath(__file__))
#Form, Base = uic.loadUiType(os.path.join(current_dir, "MainForm.ui"))

def getSerialPortNames():
    ''' Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    '''
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except PermissionError:
            pass   
        except OSError:
            pass     
        except serial.SerialException:
            pass
    return result

class MainForm(QWidget):
    def setTitleMainForm(self,title):
        self.setWindowTitle('Vibo monitoring app   '+title)
        self.buttonConnect.setEnabled(False)

    def processDevData(self,peakAcceleration,rmsAcceleration,rmsSpeed,peakFactor,KurtosisX,KurtosisY,KurtosisZ):
        self.lineEditPeakAcceleration.setText("{:10.3f}".format(peakAcceleration))#str(peakAcceleration))
        self.lineEditRMSAcceleration.setText("{:10.3f}".format(rmsAcceleration))#str(rmsAcceleration))
        self.lineEditRMSSpeed.setText("{:10.3f}".format(rmsSpeed))#str(rmsSpeed))
        self.lineEditPeakFactor.setText("{:10.3f}".format(peakFactor))#str(peakFactor))
        self.lineEditKurtosisX.setText("{:10.3f}".format(KurtosisX))#str(KurtosisX))
        self.lineEditKurtosisY.setText("{:10.3f}".format(KurtosisY))#str(KurtosisY))
        self.lineEditKurtosisZ.setText("{:10.3f}".format(KurtosisZ))#str(KurtosisZ))
        
        currentTime = datetime.datetime.now()

        if self.isRecordingStarted and self.recordFilePath!='':
            with open(self.recordFilePath,'a') as fileForRecording:
                fileForRecording.write(currentTime.date().strftime("%d.%m.%Y")+"\t")
                fileForRecording.write(currentTime.time().strftime("%H:%M:%S.%f")[:-3]+"\t")
                fileForRecording.write("{:10.6f}".format(peakAcceleration)+"\t")
                fileForRecording.write("{:10.6f}".format(rmsAcceleration)+"\t")
                fileForRecording.write("{:10.6f}".format(rmsSpeed)+"\t")
                fileForRecording.write("{:10.6f}".format(peakFactor)+"\t")
                fileForRecording.write("{:10.6f}".format(KurtosisX)+"\t")
                fileForRecording.write("{:10.6f}".format(KurtosisY)+"\t")
                fileForRecording.write("{:10.6f}".format(KurtosisZ)+"\r\n")
        
        #self.x = self.x[1:]  # Remove the first y element.
        #self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.peakVibroAccelArray = self.peakVibroAccelArray[1:]  # Remove the first
        self.peakVibroAccelArray.append(peakAcceleration)  # Add a new random value.

        self.lineRefPeakVibroAccelArray.setData(self.x, self.peakVibroAccelArray)

        self.rmsVibroAccelArray = self.rmsVibroAccelArray[1:]  # Remove the first
        self.rmsVibroAccelArray.append(rmsAcceleration)  # Add a new random value.

        self.lineRefRMSVibroAccelArray.setData(self.x, self.rmsVibroAccelArray) 

        self.rmsVibroSpeedArray = self.rmsVibroSpeedArray[1:]  # Remove the first
        self.rmsVibroSpeedArray.append(rmsSpeed)  # Add a new random value.

        self.lineRefRMSVibroSpeedArray.setData(self.x, self.rmsVibroSpeedArray) 
        '''self.queuePoints.enqueue(rmsAcceleration)
        self.graphWidgetPeakAcceleration.clear()
        self.graphWidgetPeakAcceleration.plot(self.queuePoints.getArray,pen = self.graphPen)'''

    def showMessage(self,message):
        #QtWidgets.QErrorMessage().showMessage(message)
        #errorDialog = QtWidgets.QErrorMessage()
        #errorDialog.showMessage(message)
        QMessageBox.about(self,"Warning",message)
        return

    def devConnectionClosed(self):
        self.buttonConnect.setEnabled(True)

    def comPortConnect(self):
        if self.comboBoxPortNumber.currentText()=="":
            return
        self.connector = connector()
        self.connector.setPortNumber(self.comboBoxPortNumber.currentText())
        self.connector.setBaudRate(int(self.comboBoxBaudRate.currentText(),10))
        self.connector.setModbusAddress(int(self.comboBoxModbusAddress.currentText(),16))
        self.connector.devNameReceived.connect(self.setTitleMainForm)
        self.connector.devDataReceived.connect(self.processDevData)
        self.connector.connectionClosed.connect(self.devConnectionClosed)
        self.connector.sendMessageToGui.connect(self.showMessage)
        self.buttonConnect.setEnabled(False)
        self.connector.connectDevice()

    def setNewParameters(self):
        if not self.connector.isConnected:
            return
        self.buttonSetNewParameters.setEnabled(False)
        modbusAddress  = int(self.comboBoxModbusAddress.currentText(),16)
        baudRate = int(self.comboBoxBaudRate.currentText(),10)
        self.connector.setNewParameters(modbusAddress,baudRate)

    def buttonRecordPressed(self):
        if self.buttonRecording.text()=="Start Recording":
            saveFileDialog = QFileDialog(self)
            fileName = QFileDialog.getSaveFileName(saveFileDialog,"File for recording","records/VibroStatistic.txt","Text files (*.txt)")
            if fileName[0]=='':
                return

            self.recordFilePath = fileName[0]
            '''if os.path.exists("dataTmp.txt"):
                os.remove("dataTmp.txt")'''
            self.buttonRecording.setText("Stop Recording")
            self.isRecordingStarted=True
        else:
            self.buttonRecording.setText("Start Recording")
            self.isRecordingStarted=False

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.connector.closeConnection()
        '''if os.path.exists("dataTmp.txt"):
            os.remove("dataTmp.txt")'''
        return super().closeEvent(a0)

    def __init__(self):
        super().__init__()

        self.recordFilePath = ''
        self.isRecordingStarted = False

        self.connector = connector()
        #self.queuePoints = ThreadSaveFixedQueue(1000)

        self.setFont(QFont('Arial', 12))

        mainVLayout = QVBoxLayout()

        controlPanelLayout = QHBoxLayout()
        
        vBox1=QVBoxLayout()
        self.comboBoxPortNumber = QComboBox()
        self.comboBoxPortNumber.setMinimumSize(160,24)
        vBox1.addWidget(QLabel("Port Number"))
        vBox1.addWidget(self.comboBoxPortNumber)
        ports = getSerialPortNames()
        for port in ports:
            self.comboBoxPortNumber.addItem(port)
        if ports.__len__()>0:
            self.comboBoxPortNumber.setCurrentText(ports[-1])
        controlPanelLayout.addLayout(vBox1)
        
        vBox2=QVBoxLayout()
        self.comboBoxModbusAddress = QComboBox()
        self.comboBoxModbusAddress.setMinimumSize(160,24)
        vBox2.addWidget(QLabel("Modbus Address"))
        vBox2.addWidget(self.comboBoxModbusAddress)
        for i in range(1,254):
            self.comboBoxModbusAddress.addItem("0x{:02X}".format(i))
        self.comboBoxModbusAddress.setCurrentText("0x80")
        controlPanelLayout.addLayout(vBox2)
        
        vBox3=QVBoxLayout()
        self.comboBoxBaudRate = QComboBox()
        self.comboBoxBaudRate.setMinimumSize(160,24)
        self.comboBoxBaudRate.addItem("1200")
        self.comboBoxBaudRate.addItem("2400")
        self.comboBoxBaudRate.addItem("4800")
        self.comboBoxBaudRate.addItem("9600")
        self.comboBoxBaudRate.addItem("19200")
        self.comboBoxBaudRate.addItem("38400")
        self.comboBoxBaudRate.addItem("57600")
        self.comboBoxBaudRate.addItem("115200")
        self.comboBoxBaudRate.addItem("256000")
        self.comboBoxBaudRate.addItem("512000")
        self.comboBoxBaudRate.addItem("1000000")
        self.comboBoxBaudRate.setCurrentText("115200")
        vBox3.addWidget(QLabel("Baudrate"))
        vBox3.addWidget(self.comboBoxBaudRate)
        controlPanelLayout.addLayout(vBox3)

        self.buttonConnect = QPushButton("Connect")
        self.buttonConnect.setMinimumSize(170,40)
        self.buttonConnect.clicked.connect(self.comPortConnect)
        controlPanelLayout.addWidget(self.buttonConnect)

        self.buttonSetNewParameters = QPushButton("Set New Parameters")
        self.buttonSetNewParameters.setMinimumSize(170,40)
        self.buttonSetNewParameters.clicked.connect(self.setNewParameters)
        controlPanelLayout.addWidget(self.buttonSetNewParameters)

        controlPanelLayout.addStretch(1)
        
        mainVLayout.addLayout(controlPanelLayout)

        dataPanelLayout = QHBoxLayout()

        parmetersPanelLayout = QVBoxLayout()
        dataPanelLayout.addLayout(parmetersPanelLayout)

        self.lineEditPeakAcceleration= QLineEdit()
        self.lineEditPeakAcceleration.setFixedWidth(180)
        parmetersPanelLayout.addWidget(QLabel("Peak VibroAcceleration, mg"))
        parmetersPanelLayout.addWidget(self.lineEditPeakAcceleration,0)

        self.lineEditRMSAcceleration = QLineEdit()
        self.lineEditRMSAcceleration.setFixedWidth(180)
        parmetersPanelLayout.addWidget(QLabel("RMS VibroAcceleration, mg"))
        parmetersPanelLayout.addWidget(self.lineEditRMSAcceleration,0)
        
        self.lineEditRMSSpeed = QLineEdit()
        self.lineEditRMSSpeed.setFixedWidth(180)
        parmetersPanelLayout.addWidget(QLabel("RMS VibroSpeed, mm/s^2"))
        parmetersPanelLayout.addWidget(self.lineEditRMSSpeed,0)
        
        self.lineEditPeakFactor = QLineEdit()
        self.lineEditPeakFactor.setFixedWidth(180)
        parmetersPanelLayout.addWidget(QLabel("Peak Factor"))
        parmetersPanelLayout.addWidget(self.lineEditPeakFactor,0)
        
        self.lineEditKurtosisX = QLineEdit()
        self.lineEditKurtosisX.setFixedWidth(180)
        parmetersPanelLayout.addWidget(QLabel("KurtosisX"))
        parmetersPanelLayout.addWidget(self.lineEditKurtosisX,0)
        
        self.lineEditKurtosisY = QLineEdit()
        self.lineEditKurtosisY.setFixedWidth(180)
        parmetersPanelLayout.addWidget(QLabel("KurtosisY"))
        parmetersPanelLayout.addWidget(self.lineEditKurtosisY,0)
        
        self.lineEditKurtosisZ = QLineEdit()
        self.lineEditKurtosisZ.setFixedWidth(180)
        parmetersPanelLayout.addWidget(QLabel("KurtosisZ"))
        parmetersPanelLayout.addWidget(self.lineEditKurtosisZ,0)

        self.buttonRecording = QPushButton("Start Recording")
        self.buttonRecording.setFixedSize(180,32)
        self.buttonRecording.clicked.connect(self.buttonRecordPressed)
        parmetersPanelLayout.addWidget(self.buttonRecording)
        
        '''self.lineEditCounter = QLineEdit()
        self.lineEditCounter.setFixedWidth(180)
        parmetersPanelLayout.addWidget(QLabel("counter"))
        parmetersPanelLayout.addWidget(self.lineEditCounter,0)'''
        #self.counterDataReceive = 0
        parmetersPanelLayout.addStretch(1)

        graphicsPanelLayout = QVBoxLayout()
        dataPanelLayout.addLayout(graphicsPanelLayout)

        self.graphWidgetPeakAcceleration = pg.PlotWidget()
        graphicsPanelLayout.addWidget(self.graphWidgetPeakAcceleration)
        self.graphWidgetPeakAcceleration.setBackground('w')
        
        self.graphWidgetRMSAcceleration = pg.PlotWidget()
        graphicsPanelLayout.addWidget(self.graphWidgetRMSAcceleration)
        self.graphWidgetRMSAcceleration.setBackground('w')
        
        self.graphWidgetRMSSpeed = pg.PlotWidget()
        graphicsPanelLayout.addWidget(self.graphWidgetRMSSpeed)
        self.graphWidgetRMSSpeed.setBackground('w')

        self.graphPenGreen = pg.mkPen(color = (0,255,0))
        self.graphPenBlue = pg.mkPen(color = (0,0,255))
        self.graphPenReg = pg.mkPen(color = (255,0,0))

        currentTime = datetime.datetime.now()

        self.x=list(range(400))
        self.peakVibroAccelArray=[0.0 for _ in range(400)]
        self.rmsVibroAccelArray=[0.0 for _ in range(400)]
        self.rmsVibroSpeedArray=[0.0 for _ in range(400)]
        self.lineRefPeakVibroAccelArray = self.graphWidgetPeakAcceleration.plot(self.x,self.peakVibroAccelArray,pen = self.graphPenGreen)
        self.lineRefRMSVibroAccelArray = self.graphWidgetRMSAcceleration.plot(self.x,self.rmsVibroAccelArray,pen = self.graphPenBlue)
        self.lineRefRMSVibroSpeedArray = self.graphWidgetRMSSpeed.plot(self.x,self.rmsVibroSpeedArray,pen = self.graphPenReg)
        
        '''hour = [1,2,3,4,5,6,7,8,9,10]
        temperature = [30,32,34,32,33,31,29,32,35,45]
        # plot data: x, y values
        self.graphWidgetPeakAcceleration.plot(hour, temperature,pen = self.graphPen)
        self.graphWidgetPeakAcceleration.plot(hour)'''

        mainVLayout.addLayout(dataPanelLayout)
        self.setLayout(mainVLayout)

        self.setGeometry(0,0,800,480)
        self.setMinimumHeight(480)
        self.setWindowTitle('Vibo monitoring app')

        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainForm()
    sys.exit(app.exec_())