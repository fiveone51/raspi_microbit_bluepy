# raspi_microbit_bluepy
Raspberry pi で、BLEを使うためのライブラリとしてはいろいろあるが、個人的に bluepy が一番わかりやすかったため、設定方法・使い方などをメモしておく。また、サンプルとして、micro:bit をコントロールする。

**環境**

* raspberry pi Zero W  or raspberry pi 3 など
* raspbian-stretch
* python or python3
* micro:bit  (ただし、micro:bit を BLEペリフェラルモードで起動するためには、micro:bit側に設定が必要。その方法は Google先生に「[micro:bit BLE](https://www.google.co.jp/search?q=micro%3Abit+BLE)」で聞くと、すぐに教えてくれるので、ここでは省略。）

## Raspberry pi へのインストール
bluepyは標準ではインストールされていないので、手動でインストールする必要がある。基本は、apt, python-pip などのパッケージ利用する。

````
# python2 の場合

$ sudo apt install libbluetooth3-dev libglib2.0 libboost-python-dev libboost-thread-dev
$ sudo apt install python-pip
$ sudo pip install gattlib
$ sudo pip install bluepy
$ sudo systemctl daemon-reload
$ sudo service bluetooth restart
````
````
# python3 の場合

$ sudo apt install libbluetooth3-dev libglib2.0 libboost-python-dev libboost-thread-dev
$ sudo apt install python3-pip
$ cd /usr/lib/arm-linux-gnueabihf/
$ sudo ln libboost_python-py35.so libboost_python-py34.so
$ sudo pip3 install gattlib
$ sudo pip3 install bluepy
$ sudo systemctl daemon-reload
$ sudo service bluetooth restart
````

python3 の場合、バージョンの整合性があっていないのか、3,4行目のようにファイルの作成を行わないと、gattlib のインストールでエラーになってしまう。


## デバイスをスキャンして、micro:bit を見つける

インストールできたら、動作確認もかねて、デバイスのスキャンを行い、micro:bit を見つける。当然、micro:bit をBLEペリフェラルモードで起動しておく必要がある。

以降のソースは、python3 で動作確認済み。

````scan.py
import bluepy

scanner = bluepy.btle.Scanner(0)
devices = scanner.scan(3)      # 3秒間スキャンする

for device in devices:
  print('======================================================')
  print('address : %s' % device.addr)
  print('addrType: %s' % device.addrType)
  print('RSSI    : %s' % device.rssi)
  print('Adv data:')
  for (adtype, desc, value) in device.getScanData():
    print(' (%3s) %s : %s ' % (adtype, desc, value))
````
**SCAN操作だけは、root で行う必要がある。** 他は一般ユーザでOK

````
$ sudo python3 scan.py
======================================================
address : **:**:**:**:**:**                       ← 本当はちゃんとしたアドレスが表示される
addrType: random
RSSI    : -47
Adv data:
 (  1) Flags : 06
 (  9) Complete Local Name : BBC micro:bit [tezep]
======================================================
address : **:**:**:**:**:**
addrType: random
RSSI    : -92
Adv data:
 (  1) Flags : 1a
 (255) Manufacturer : **************************************************
======================================================
address : **:**:**:**:**:**
addrType: random
RSSI    : -75
Adv data:
 (  1) Flags : 06
 (  9) Complete Local Name : toio Core Cube
 (  7) Complete 128b Services : 10b20100-5b3b-4571-9508-cf3efcd7bbae :
======================================================
(以降、デバイス分続く)
:
````

我が家の環境では、上記のようなデバイスが、10個ぐらい出力された。マンションなので、周辺の部屋のデバイスだと思うが・・・。
これらの情報のうち、Adv data に、デバイスを特定するための情報が出力されるので、この情報をもとに、micro:bit （上記の例では、1つ目のデバイス）の「address」と「addrType」を確認しておく（後で使うため）。
ちなみに、「RSSI」は電波強度を表していて、数値が大きい方が、近くにあると考えてよい（上記の3つのデバイスでいうと、micro:bit が一番近くにあるということ）。「Adv data」の情報でデバイスが特定できない場合は、場所を移動させて、RSSIの値をもとに特定すればよい。

## GATT Handle を調べる

bluepy で、特性にコマンドを送ったり、読み取りしたりする際には、GATT Handle と呼ばれる値を使って行うのが簡単。BLEデバイスの特性を公開する際は、特性UUID で説明されていることが多く、GATT Handle はなかなか公開されていない。そこで、bluepy を使って、デバイスの特性UUIDとGATT Handle を調べておく。

まずは、調べるデバイスについての addressとaddrType が必要なので、先のscan.py の出力から、micro:bit を特定し、address と addrType を確認しておく。
以下の例では、micro:bit の address を第一引数で指定して、micro:bit の特性UUID/GATT Handleを調べている。

````getHandle.py
import sys
import bluepy

def main():
    try:
        peri = bluepy.btle.Peripheral()
        peri.connect(devadr, bluepy.btle.ADDR_TYPE_RANDOM)  # addrTypeがpublic なら、ADDR_TYPE_PUBLICを指定
    except:
        print("device connect error")
        sys.exit()

    charas = peri.getCharacteristics()
    for chara in charas:
        print("======================================================")
        print(" UUID : %s" % chara.uuid )
        print(" Handle %04x: %s" % (chara.getHandle(), chara.propertiesToString()))

    peri.disconnect()

if __name__ == "__main__":
    if len(sys.argv) == 1:
      print('Usage: getHandle.py BLE_DEVICE_ADDRESS')
      sys.exit()
    devadr = sys.argv[1]

    main()
````
````
$ python3 getHandle.py **:**:**:**:**:**                      ←　実際には、micro:bit の address を指定
======================================================
 UUID : 00002a00-0000-1000-8000-00805f9b34fb
 Handle 0003: READ WRITE
======================================================
 UUID : 00002a01-0000-1000-8000-00805f9b34fb
 Handle 0005: READ
======================================================
 UUID : 00002a04-0000-1000-8000-00805f9b34fb
 Handle 0007: READ
======================================================
 UUID : 00002a05-0000-1000-8000-00805f9b34fb
 Handle 000a: INDICATE
======================================================
 UUID : e95d93b1-251d-470a-a062-fa1922dfa9a8
 Handle 000e: READ WRITE
======================================================
 UUID : 00002a24-0000-1000-8000-00805f9b34fb
 Handle 0011: READ
======================================================
 UUID : 00002a25-0000-1000-8000-00805f9b34fb
 Handle 0013: READ
======================================================
 UUID : 00002a26-0000-1000-8000-00805f9b34fb
 Handle 0015: READ
======================================================
 UUID : e95d9775-251d-470a-a062-fa1922dfa9a8
 Handle 0018: NOTIFY READ
======================================================
:
````

ここまでで、デバイスについて以下の情報が分かった。

* address
* addrType
* 特性UUID の一覧
* 特性のGATT Handle

addressとaddrType を使って、デバイスを特定し、接続することができる。
特性UUIDは、デバイスが提供するサービスについての情報のキーになる。
特性を利用するときに、GATT Handle を使って、利用したい特性を指定し、コマンドを送受信させる。

## bluepy を使って、micro:bit に命令を送ってみる

ここからが本命で、BLEデバイスの基本的な使い方として、

* write
* read
* notify

の3種類の使い方を説明する。

### micro:bit のLED を制御（write）

micro:bit には、LEDにアスキー文字をスクロールさせて表示させるサービスがある。こちらを利用して、"Hello world"と表示させる。
[micro:bitのプロファイルのサイト](https://lancaster-university.github.io/microbit-docs/resources/bluetooth/bluetooth_profile.html)  から、LEDに文字列を表示させるサービスの特性UUIDを調べると、「E95D93EE251D470AA062FA1922DFA9A8」だと分かる。
先の実行結果の中に

````
======================================================
 UUID : e95d93ee-251d-470a-a062-fa1922dfa9a8
 Handle 003c: READ WRITE
======================================================
````

という行があるので、GATT Handle は、「0x003c」であることが分かる。
最低限、以下のコードで、micro:bit に命令を送ることができる。
BLE命令のフォーマットなども、[参考サイト](https://lancaster-university.github.io/microbit-docs/resources/bluetooth/bluetooth_profile.html)に記載されている。

````writeLed.py
import time
import bluepy

HANDLE_LED = 0x003c
devadr = "**:**:**:**:**:**"   # 実際にはmicro:bit のアドレスを記述

def main():
    peri = bluepy.btle.Peripheral()
    peri.connect(devadr, bluepy.btle.ADDR_TYPE_RANDOM)
    peri.writeCharacteristic(HANDLE_LED, b'Hello World' )
    time.sleep(5)
    peri.disconnect()

if __name__ == "__main__":
    main()
````

main()の中で、オブジェクトを作って、接続して、命令をbytes型で送って、接続解除、という非常に簡単な命令で micro:bit を操作することができた。

### micro:bit から情報を読み込む（read）

デバイスからの読込みも簡単。
micro:bit のデバイス名と、シリアル番号を取り出すためには、以下の特性を利用する。

|特性|特性UUID|GATT Handle|
|:---|:---|:----|
|Device Name|00002A0000001000800000805F9B34FB|0x0003|
|Serial Number String|00002A2500001000800000805F9B34FB|0x0013|

````getvalue.py
import bluepy

HANDLE_DEVNAME = 0x0003
HANDLE_SERIAL = 0x0013

devadr = "**:**:**:**:**:**"   # 実際にはmicro:bit のアドレスを記述

def main():
    peri = bluepy.btle.Peripheral()
    peri.connect(devadr, bluepy.btle.ADDR_TYPE_RANDOM)
    devname = peri.readCharacteristic(HANDLE_DEVNAME)
    print( "Device Name: %s" % devname )
    serialnum = peri.readCharacteristic(HANDLE_SERIAL)
    print( "Serial Number: %s" % serialnum )
    peri.disconnect()

if __name__ == "__main__":
    main()
````
````
$ python3 getvalue.py
Device Name: b'BBC micro:bit [tezep]'
Serial Number: b'306452****'
````

writeの時との違いは、writeがreadになったところぐらい。


### micro:bit のボタン通知を受け取る（notify）

notify は、デバイスからの通知を受ける方法。例えば、micro:bit にあるAボタン、Bボタンが押されたときに通知を受け取る、というようなもの。通知の際には、デバイスからそれなりのデータも送られてくる。

やり方としては、大まかに以下のような感じ。

* Notifyが発生したときに実行するクラスを定義する（Delegateクラスを定義）
* 通知要求の設定
* ループなどでNotify まち

|属性|特性UUID|GATT Handle|
|:---|:---|:----|
|Button A State|E95DDA90251D470AA062FA1922DFA9A8|0x0029|
|Button B State|E95DDA91251D470AA062FA1922DFA9A8|0x002c|

micro:bit のButtonサービスでは、ボタンのON, OFF, 長押しのタイミングで、notifyを返すとのこと。

````notify.py
import bluepy
import binascii

HANDLE_A_BUTTON = 0x0029
HANDLE_B_BUTTON = 0x002c
devadr = "**:**:**:**:**:**"   # 実際にはmicro:bit のアドレスを記述

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
    main()
````
* Notifyが発生したときに実行するクラスを定義する（Delegateクラスを定義）

MyDelegate クラスとして定義する。デバイスから通知が送られてきたときに、handleNotificationメソッドが実行される。
このメソッドが実行されるときには、呼び出し元の特性GATT Handleと、送られてきたデータが渡されるので、それを元に処理を行えばよい。上記の例では、通知が送られてきた特性の名前を保存し、送られてきたデータから、通知が長押しであれば、ループを終了させている。

* 通知要求の設定

通知要求を設定するときには、通知してほしい特性GATT Handleに「**+1**」した Handle に対して、1 (\x01\x00) を書き込む。通知要求を解除するときには、GATT Handleに「**+1**」した Handle に対して、0 (\x00\x00) を書き込む。

* ループなどでNotify 待ち

標準で、waitForNotificationsメソッドがあるので、こちらをループ内に仕掛ける。

````
実行例
$ python3 notify.py
Notification を待機。A or B ボタン長押しでプログラム終了
button B: b'01'
button B: b'00'
button A: b'01'
button A: b'00'
button B: b'01'
button B: b'02'
````

## 参考サイト
* [bluepyのドキュメント](http://ianharvey.github.io/bluepy-doc/index.html)
* [micro:bitのプロファイル](https://lancaster-university.github.io/microbit-docs/resources/bluetooth/bluetooth_profile.html)  
