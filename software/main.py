from TM1650 import *
from TM7705 import *
from machine import Pin, I2C
import utime


def calibration_zero():
    result_list = []
    for i in range(10):
        tm1650.display(str(9 - i)*4)
        result_list.append(tm7705.get_adc_result())
    result_list.sort()
    return (result_list[4] + result_list[5])/2


tm1650 = TM1650(I2C(0, scl=Pin(1), sda=Pin(0), freq=100000))
tm7705 = TM7705(sck_id=2, mosi_id=3, miso_id=4, cs_id=5, ok_id=6)

# 配置tm7705和tm1650
tm7705.ref_volt(3.3)
tm7705.pga(1)
tm7705.channel(1)
tm7705.input_type('b')
tm7705.prepare_ad_conv(1_000_000)
tm7705.self_calibration()
tm1650.brightness(0)

# 按键和LED
key_set = Pin(18, Pin.IN, Pin.PULL_UP)

RGB_LED1_Anode = Pin(14, Pin.OUT)
RGB_LED1_Red_Cathode = Pin(16, Pin.OUT)
RGB_LED1_Green_Cathode = Pin(17, Pin.OUT)
RGB_LED1_Blue_Cathode = Pin(15, Pin.OUT)
RGB_LED1_Anode.value(1)
RGB_LED1_Red_Cathode.value(1)
RGB_LED1_Green_Cathode.value(1)
RGB_LED1_Blue_Cathode.value(1)

RGB_LED2_Anode = Pin(10, Pin.OUT)
RGB_LED2_Red_Cathode = Pin(12, Pin.OUT)
RGB_LED2_Green_Cathode = Pin(13, Pin.OUT)
RGB_LED2_Blue_Cathode = Pin(11, Pin.OUT)
RGB_LED2_Anode.value(1)
RGB_LED2_Red_Cathode.value(1)
RGB_LED2_Green_Cathode.value(1)
RGB_LED2_Blue_Cathode.value(1)


# 校准
color = 0  # RGB2随时间变色
while key_set.value() != 0:
    color += 1
    color = color % 3
    if color == 0:
        RGB_LED2_Red_Cathode.value(0)
        RGB_LED2_Green_Cathode.value(1)
        RGB_LED2_Blue_Cathode.value(1)
    elif color == 1:
        RGB_LED2_Red_Cathode.value(1)
        RGB_LED2_Green_Cathode.value(0)
        RGB_LED2_Blue_Cathode.value(1)
    else:
        RGB_LED2_Red_Cathode.value(1)
        RGB_LED2_Green_Cathode.value(1)
        RGB_LED2_Blue_Cathode.value(0)
    utime.sleep_ms(100)

RGB_LED2_Red_Cathode.value(1)
RGB_LED2_Green_Cathode.value(1)
RGB_LED2_Blue_Cathode.value(1)

default_volt = -calibration_zero()


# 开始测量
while 1:
    result = -(tm7705.get_adc_result()) - default_volt  # 硬件接反了，软件补救一下
    print("result is {:8.4f} V".format(result))
    if result > 0:  # 磁场和标注的同向
        # 红色
        RGB_LED1_Red_Cathode.value(0)
        RGB_LED1_Green_Cathode.value(1)
        RGB_LED1_Blue_Cathode.value(1)

        # 计算场强 1mV/Gs @ 3.3V 10 Gs = 1 mT => 1 mV = 0.1 mT
        result_mv = result * 1000
        mag_gs = result_mv * 1
        mag_mt = mag_gs / 10
        print(
            "corrent magnetic flux density is {:8.4f} mT, direction: positive".format(mag_mt))
    elif result < 0:
        result = -result
        # 蓝色
        RGB_LED1_Red_Cathode.value(1)
        RGB_LED1_Green_Cathode.value(1)
        RGB_LED1_Blue_Cathode.value(0)

        # 计算场强 1mV/Gs @ 3.3V 10 Gs = 1 mT
        result_mv = result * 1000
        mag_gs = result_mv * 1
        mag_mt = mag_gs / 10
        print(
            "corrent magnetic flux density is {:8.4f} mT, direction: negative".format(mag_mt))
    else:
        # 绿色
        RGB_LED1_Red_Cathode.value(1)
        RGB_LED1_Green_Cathode.value(0)
        RGB_LED1_Blue_Cathode.value(1)
        print("corrent magnetic flux density is 0 mT")
        mag_mt = 0.0

    if mag_mt >= 150: # 最大±1.6V压差，对应160mT
        str_mag_mt  = '    '
    elif mag_mt > 0.005:
        str_mag_mt = str(mag_mt)[0:5]
    else:
        str_mag_mt = '0.000'

    print(str_mag_mt)
    tm1650.display(str_mag_mt)
    if key_set.value() == 0:
        RGB_LED1_Red_Cathode.value(1)
        RGB_LED1_Green_Cathode.value(1)
        RGB_LED1_Blue_Cathode.value(1)
        tm1650.display('    ')
        default_volt = -calibration_zero()
