
def modbusAsciiCRC(bytes):
    sumB = sum(bytes)&0xFF
    result = 0xFF - sumB +1
    return result

def getInfoRequest(modbusAddress):
    bytes = [modbusAddress,0x11]
    crc = modbusAsciiCRC(bytes)
    bytes.append(crc)
    return ":" + ''.join(format(x, '02X') for x in bytes)+"\r\n"

def getInputRegistersRequest(modbusAddress,startRegister,numberOfRegisters):
    bytes = [modbusAddress,0x04,(startRegister>>8)&0xFF,startRegister&0xFF,(numberOfRegisters>>8)&0xFF,numberOfRegisters&0xFF]
    crc = modbusAsciiCRC(bytes)
    bytes.append(crc)
    return ":" + ''.join(format(x, '02X') for x in bytes)+"\r\n"

def getHoldingRegistersRequest(modbusAddress,startRegister,numberOfRegisters):
    bytes = [modbusAddress,0x03,(startRegister>>8)&0xFF,startRegister&0xFF,(numberOfRegisters>>8)&0xFF,numberOfRegisters&0xFF]
    crc = modbusAsciiCRC(bytes)
    bytes.append(crc)
    return ":" + ''.join(format(x, '02X') for x in bytes)+"\r\n"

def setHoldingRegistersRequest(modbusAddress,startRegister,registers):
    registerCount = registers.__len__()
    bytes = [modbusAddress,0x10,(startRegister>>8)&0xFF,startRegister&0xFF,(registerCount>>8)&0xFF,registerCount&0xFF,registerCount*2]

    for reg in registers:
        bytes.append(reg&0xFF)
        bytes.append((reg>>8)&0xFF)

    crc = modbusAsciiCRC(bytes)
    bytes.append(crc)
    return ":" + ''.join(format(x, '02X') for x in bytes)+"\r\n"

if __name__ == '__main__':
    str1 = setHoldingRegistersRequest(0x80,4,[0x0002,])
    print(str1)

