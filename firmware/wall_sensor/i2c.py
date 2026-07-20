import machine
import utime

sdaPIN = machine.Pin(0)
sclPIN = machine.Pin(1)
i2c = machine.I2C(0, sda=sdaPIN, scl=sclPIN, freq=400000)
devices = i2c.scan()

found = False


def reg_write(i2c, addr, reg, data):
    """
    Write bytes to the specified register.
    """

    # Construct message
    msg = bytearray()
    msg.append(data)

    # Write out message to register
    i2c.writeto_mem(addr, reg, msg)


def reg_read(i2c, addr, reg, nbytes=1):
    """
    Read byte(s) from specified register. If nbytes > 1, read from consecutive
    registers.
    """

    # Check to make sure caller is asking for 1 or more bytes
    if nbytes < 1:
        return bytearray()

    # Request data from specified register(s) over I2C
    data = i2c.readfrom_mem(addr, reg, nbytes)

    return data


while not found:
    if len(devices) != 0:
        print("Number of I2C devices found=", len(devices))
        found = True
        for device in devices:
            print("Device Hexadecimel Address= ", hex(device))
    else:
        print("No device found")
        utime.sleep(1)

data = i2c.readfrom_mem(0x18, 0x05, 2)
ctemp = ((data[0] & 0x1F) * 256) + data[1]

if ctemp > 4095:

    ctemp -= 8192

ctemp = ctemp * 0.0625

ftemp = ctemp * 1.8 + 32

print(ctemp)
print(ftemp)

# DEV_ADDR = 0x36
# RAWANGLE = 0x0c
# ANGLE = 0x0b
# STATUS = 0x0b

# while True:
#    data = reg_read(i2c, DEV_ADDR, STATUS, 1)
#    print("".join("\\x%02x" % i for i in data))
#    data = reg_read(i2c, DEV_ADDR, RAWANGLE, 2)
#    print("".join("\\x%02x" % i for i in data))
#    word = (data[0] << 8) + data[1]
#    print(word)
#    deg = (360/4096) * word
#    print(deg)
# data = reg_read(i2c, DEV_ADDR, STATUS, 1)
# print(data)
#    utime.sleep(0.5)
