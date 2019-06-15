import bluepy
import binascii

HANDLE_A_BUTTON = 0x0029
HANDLE_B_BUTTON = 0x002c

exflag = False

class MyDelegate(bluepy.btle.DefaultDelegate):
    def __init__(self, params):
        bluepy.btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        global exflag

        if cHandle == HANDLE_A_BUTTON:
            b = "button A"
            if data[0] == 0x02:   # ボタン長押し
                exflag = True
        if cHandle == HANDLE_B_BUTTON:
            b = "button B"
            if data[0] == 0x02:
                exflag = True

        c_data = binascii.b2a_hex(data)
        print( "%s: %s" % (b, c_data) )

def main():
    peri = bluepy.btle.Peripheral()
    peri.connect(devadr, bluepy.btle.ADDR_TYPE_RANDOM)
    peri.withDelegate(MyDelegate(bluepy.btle.DefaultDelegate))

    # ボタン notify を要求
    peri.writeCharacteristic(HANDLE_A_BUTTON + 1, b'\x01\x00')
    peri.writeCharacteristic(HANDLE_B_BUTTON + 1, b'\x01\x00')

    print( "Notification を待機。A or B ボタン長押しでプログラム終了")
    while exflag == False:
        if peri.waitForNotifications(1.0):
            continue
    peri.disconnect()

if __name__ == "__main__":
    if len(sys.argv) == 1:
      print('Usage: getHandle.py BLE_DEVICE_ADDRESS')
      sys.exit()
    devadr = sys.argv[1]

    main()
