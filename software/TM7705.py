from machine import Pin, SPI
import utime

"""
DEV NOTE:
1. 目前不清楚滤波同步的作用，使能后就不工作了，需要观察，有机会尝试交错通道采样观察效果 I don't know how fiter synchronization work, and when enable fsysn, adc stop convert
2. 频率寄存器只能写80H或者84H，测试下来1MHz时钟不用80H输出有问题 The clock register can't be written into data expect 0x80 or 0x84
"""


class TM7705:
    """
    class TM7705 is designed to operate TM7705 by RPi Pico with micropython.

    TM7705 is a 16bit sigma-delta ADC, similar to AD7705, but much cheaper than it. Due to its structure,
    it works in a very low speed, so this class choose using soft SPI to drive this chip.

    How to use:

    0. initializaton
    1. set reference voltage/PGA/channel/input type (bipolar or unipolar)
    2. perpare for AD convert (write all data into registers)
    3. do self-calobration
    4. get adc result
    """
    # pin def
    _sck = None
    _mosi = None
    _miso = None
    _cs = None
    _ok = None
    _reset = None
    # config para
    _ref_volt = -1
    _channel = 1
    _pga = 1
    _input_type = 'bipolar'  # unipolar or bipolar

    def __init__(self, sck_id, mosi_id, miso_id, cs_id, ok_id, reset_id=None):
        """initialize the chip, if reset pin is not connected to mcu gpio, just keep None"""
        self._cs = Pin(cs_id, Pin.OUT)
        self._ok = Pin(ok_id, Pin.IN, Pin.PULL_UP)
        self._mosi = Pin(mosi_id, Pin.OUT)
        self._miso = Pin(miso_id, Pin.IN, Pin.PULL_UP)
        self._sck = Pin(sck_id, Pin.OUT)
        if reset_id is None:
            self._reset = None
        else:
            self._reset = Pin(reset_id, Pin.OUT)

        self._cs.value(1)
        self._mosi.value(1)
        self._sck.value(1)
        self.reset()
        # soft reset, won't return to default value but return to after-reset status on communication, 
        # if last communication is not ended correctly, soft reset help return to correct status
        self.__select__()
        self.__send_byte__(0xff)
        self.__send_byte__(0xff)
        self.__send_byte__(0xff)
        self.__send_byte__(0xff)
        self.__send_byte__(0xff)
        self.__release__()

    def __select__(self):
        """select the chip"""
        self._sck.value(1)
        self._cs.value(0)

    def __release__(self):
        """release the chip"""
        self._cs.value(1)

    def __send_byte__(self, data):
        """send 8 bit data to the chip"""
        self._sck.value(1)
        for i in range(8):
            self._sck.value(0)
            if data & (0x80 >> i):
                self._mosi.value(1)
            else:
                self._mosi.value(0)
            self._sck.value(1)  # adc get the data at the rising edge
        self._sck.value(1)
        self._mosi.value(1)

    def __get_byte__(self):
        """get 8 bit data from the chip"""
        data = 0x00
        self._sck.value(1)
        for i in range(8):
            self._sck.value(0)  # the master get the data at the falling edge
            if self._miso.value() == 1:
                data |= (0x80 >> i)
            self._sck.value(1)
        self._sck.value(1)
        return data

    def __set_register__(self, reg_addr, data):
        """set the data to target register\n
        warning: will select a channel if no channel is selected\n
        addr | name       | length | chinese name\n
        0    communication 8       通讯寄存器\n
        1    setup         8       配置寄存器\n
        2    clock         8       频率寄存器\n
        3    data          16      adc结果寄存器 \n
        4    test          8       测试寄存器\n
        5    no_opration   0       NC寄存器\n
        6    offset        24      零点漂移寄存器\n
        7    gain          24      增益系数寄存器\n"""
        if reg_addr not in [1, 2, 6, 7]:
            print("invalid reg addr")
            return

        # communicate with communication reg
        self.__select__()
        if self._channel == 2:
            # select the reg @ ch2, read
            self.__send_byte__(0x01 | reg_addr << 4)
        else:
            # select the reg @ ch1, read
            self.__send_byte__(0x00 | reg_addr << 4)
        self.__release__()

        # try set the data to target reg
        self.__select__()
        if reg_addr in [1, 2]:
            self.__send_byte__(data)
        else:
            print("offset/gain reg is not supported to set the data yet")
        self.__release__()

    def __read_from_register__(self, reg_addr):
        """read data from register\n
        warning: will select a channel if no channel is selected\n
        addr | name       | length | chinese name\n
        0    communication 8       通讯寄存器\n
        1    setup         8       配置寄存器\n
        2    clock         8       频率寄存器\n
        3    data          16      adc结果寄存器 \n
        4    test          8       测试寄存器\n
        5    no_opration   0       NC寄存器\n
        6    offset        24      零点漂移寄存器\n
        7    gain          24      增益系数寄存器\n"""
        # communicate with communication reg
        if reg_addr not in [0, 1, 2, 4, 6, 7]:
            print("invalid reg addr")
            return

        self.__select__()
        if self._channel == 2:
            # select the reg @ ch2, read
            self.__send_byte__(0x09 | reg_addr << 4)
        else:
            # select the reg @ ch1, read
            self.__send_byte__(0x08 | reg_addr << 4)
        self.__release__()
        # try get data
        data = 0
        self.__select__()
        if reg_addr in [0, 1, 2, 4]:
            data = self.__get_byte__()
        elif reg_addr in [6, 7]:
            data = self.__get_byte__()
            data = data << 8
            data += self.__get_byte__()
            data = data << 8
            data += self.__get_byte__()
        else:
            data = -1
        self.__release__()
        return data

    def __decode_adc_value__(self, adc_data):
        """decode the adc value to volt"""
        if self._input_type == 'bipolar' or self._input_type == 'b':
            return (adc_data/32768 - 1) * self._ref_volt / self._pga
        else:
            return (adc_data/65536) * self._ref_volt / self._pga

    def test(self):
        """test the spi bus, try read the 8-bit reg"""
        for addr in [0, 1, 2, 4]:
            data = self.__read_from_register__(addr)
            print("reg address is {:d}, data is {:d}".format(addr, data))
            self.__release__()

    def reset(self):
        """hardware reset, return all registers to default value, require a io linked to reset pin"""
        if self._reset is not None:
            self._reset.value(0)
            utime.sleep_ms(10)
            self._reset.value(1)
            utime.sleep_ms(10)
        else:
            print("no hardware connection to reset pin")

    def ref_volt(self, ref_volt=-1):
        """get / set the reference voltage (V)"""
        if ref_volt == -1:  # try get reference voltage
            if self._ref_volt != -1:
                return self._ref_volt
            else:
                print("reference voltage is not initialized")
                return -1
        else:
            if 0 <= ref_volt <= 5.5:
                self._ref_volt = ref_volt
            else:
                print("reference voltage out of range")

    def pga(self, pga=-1):
        """get / set the PGA"""
        if pga == -1:  # try get reference voltage
            return self._pga
        else:
            if pga in [1, 2, 4, 8, 16, 32, 64, 128]:
                self._pga = pga
            else:
                print("invalid PGA")

    def channel(self, channel=-1):
        """get / set the channel to ad convert"""
        if channel == -1:
            if self._channel != -1:
                return self._channel
            else:
                print("ad channel is not initialized")
        else:
            if channel == 1 or channel == 2:
                self._channel = channel
            else:
                print("invalid channel id")

    def input_type(self, input_type=''):
        """"get / set the input type (bipolar(b)/unipolar(u))"""
        if input_type == '':
            return self._input_type
        elif input_type == 'b' or input_type == 'bipolar':
            self._input_type = 'bipolar'
        elif input_type == 'u' or input_type == 'unipolar':
            self._input_type = 'unipolar'
        else:
            print("invalid input")

    def self_calibration(self):
        """ do self calibration"""
        self.__set_register__(1, 0x40)
        utime.sleep_ms(1)
        max_wait = 99
        while self._ok.value() != 0 and max_wait <= 0:
            max_wait -= 1
            utime.sleep_ms(1)
        print("self calibration cost {:d} ms".format(100-max_wait))
        print("self calibration finished")

    def prepare_ad_conv(self, osc_freq):
        """prepare for AD convert, write all data to registers"""
        # setup reg
        data = 0
        if self._pga == 1:
            data = 0b00_000_0_0_0  # disable fsync
        elif self._pga == 2:
            data = 0b00_001_0_0_0
        elif self._pga == 4:
            data = 0b00_010_0_0_0
        elif self._pga == 8:
            data = 0b00_011_0_0_0
        elif self._pga == 16:
            data = 0b00_100_0_0_0
        elif self._pga == 32:
            data = 0b00_101_0_0_0
        elif self._pga == 64:
            data = 0b00_110_0_0_0
        elif self._pga == 128:
            data = 0b00_111_0_0_0
        else:
            data = 0x00
            print("a error occured in preparing ad conv")

        if self._input_type == 'bipolar' or self._input_type == 'b':
            data |= 0b00_000_0_0_0
        else:  # unipolar
            data |= 0b00_000_1_0_0

        self.__set_register__(1, data=data)

        # clock reg
        if 400_000 <= osc_freq <= 1_400_000:
            self.__set_register__(2, 0x80)
        elif 1_600_000 <= osc_freq <= 2_500_000:
            self.__set_register__(2, 0x84)
        else:
            self.__set_register__(2, 0x80)

    def get_adc_result(self, timeout_ms=5000):
        """try get adc result and decode into volt"""
        self.__select__()
        if self._channel == 2:
            self.__send_byte__(0x39)
        else:
            self.__send_byte__(0x38)
        self.__release__()

        check_time = timeout_ms // 10
        finished = False
        while timeout_ms >= 0:
            if self._ok.value() == 0:  # ad conv is finished
                finished = True
                break
            else:
                timeout_ms -= check_time
                utime.sleep_ms(check_time)

        if finished:
            self.__select__()
            adc_data1 = self.__get_byte__()
            adc_data2 = self.__get_byte__()
            self.__release__()
            adc_data = adc_data1*256 + adc_data2
            # print("0x{:04x}".format(adc_data))
            return self.__decode_adc_value__(adc_data)
        else:
            print("failed to get adc result: time out")
            return 114514.1919


if __name__ == "__main__":
    tm7705 = TM7705(sck_id=2, mosi_id=3, miso_id=4,
                    cs_id=5, ok_id=6)
    tm7705.test()
    tm7705.ref_volt(3.3)
    tm7705.pga(1)
    print("pga = {:d}".format(tm7705.pga()))
    tm7705.channel(1)
    tm7705.input_type('b')
    print(tm7705.input_type())
    tm7705.prepare_ad_conv(1_000_000)
    tm7705.self_calibration()

    for i in range(1, 101):
        result = tm7705.get_adc_result()
        print("index {:d} result {:8.4f}V".format(i, result))
