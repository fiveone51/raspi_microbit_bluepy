import time
import bluepy

HANDLE_LED = 0x003c

def main():
    peri = bluepy.btle.Peripheral()
    peri.connect(devadr, bluepy.btle.ADDR_TYPE_RANDOM)
    peri.writeCharacteristic(HANDLE_LED, b'Hello World' )
    time.sleep(5)
    peri.disconnect()

if __name__ == "__main__":
    if len(sys.argv) == 1:
      print('Usage: getHandle.py BLE_DEVICE_ADDRESS')
      sys.exit()
    devadr = sys.argv[1]

    main()
