from machine import Pin, I2C
import utime

class TM1650:
    """
    class TM1650 is designed to operate TM1650 by RPi Pico with micropython.
    This class currently can only use tm1650 to drive 4-bit LED Digits (7-Segments, common cathode).

    TM1650 is a LED driver & keyboard scan ASIC, using IIC to communicate.

    How to use:

    0. initialization
    1. set the brightness
    2. input a string of 4 digits for display
    """
    digit_code = {
        '0': 0x3f,
        '1': 0x06,
        '2': 0x5b,
        '3': 0x4f,
        '4': 0x66,
        '5': 0x6d,
        '6': 0x7d,
        '7': 0x07,
        '8': 0x7f,
        '9': 0x6f,
        '.': 0x80,
        ' ': 0x00
    }
    i2c = None
    def __init__(self,i2c):
        self.i2c = i2c
        addr_list = self.i2c.scan()
        if (0x68>>1 in addr_list) and (0x6a>>1 in addr_list) and (0x6c>>1 in addr_list) and (0x6e>>1 in addr_list):
            print("TM1650 Found!")
            
        self.brightness(0) # 设置为最亮
        self.i2c.writeto(0x68>>1, b'\x4E')
        self.i2c.writeto(0x6a>>1, b'\x4E')
        self.i2c.writeto(0x6c>>1, b'\x4E')
        self.i2c.writeto(0x6e>>1, b'\x4E')
        
        
    def brightness(self,b):
        """Set the brightness, 0 for the most bright, LED brightness increases form 1 to 7"""
        t = (b<<4) | 0x01
        self.i2c.writeto(0x48>>1,t.to_bytes(1,'big')) # 强制开显示
        
    def display(self,num_str):
        """decode the num_str into display code, than send the code to tm1650, the num_str should be a string include 4
        digits and sometimes a point, so the length of num_str should be 4 or 5"""
        if len(num_str) < 4 or len(num_str) > 5:
            print("invalid input string")
            return
        
        disp_list = [0x00] * 4
        index = 0 # 处理第index个数字
        for i in range(len(num_str)):
            if num_str[i] == '.':
                index -= 1
                disp_list[index] |= self.digit_code['.']
                index += 1
            elif num_str[i] in self.digit_code:
                disp_list[index] = self.digit_code[num_str[i]]
                index += 1
            else:
                disp_list[index] = self.digit_code[' ']
                index += 1
        
        self.i2c.writeto(0x68>>1, disp_list[0].to_bytes(1,'big'))
        self.i2c.writeto(0x6a>>1, disp_list[1].to_bytes(1,'big'))
        self.i2c.writeto(0x6c>>1, disp_list[2].to_bytes(1,'big'))
        self.i2c.writeto(0x6e>>1, disp_list[3].to_bytes(1,'big'))
        
        
        
if __name__ == "__main__":
    tm1650 = TM1650(I2C(0, scl=Pin(1), sda=Pin(0),freq=100000))
    b = 0
    for i in range(1000,10000):
        b = (b+1)%8
        tm1650.brightness(b)
        tm1650.display(str(i/100))
        utime.sleep(0.05)
        
        
        
    