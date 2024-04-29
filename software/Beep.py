from machine import Pin, PWM
import utime

class Beep:
    pwm = None
    def __init__(self,beep_pin):
        """初始化PWM引脚"""
        self.pwm = PWM(Pin(beep_pin))
        self.pwm.freq(440)
        self.pwm.duty_u16(0)
        
    def play(self,freq,ms):
        self.pwm.freq(freq)
        self.pwm.duty_u16(32767)
        utime.sleep_ms(ms)
        self.pwm.duty_u16(0)
        

if __name__ == "__main__":
    beep = Beep(28)
    scales_5 = {
        'C': 523,
        'C#': 554,
        'D': 587,
        'Eb': 622,
        'E': 659,
        'F': 698,
        'F#': 740,
        'G': 784,
        'G#': 831,
        'A': 880,
        'Bb': 932,
        'B': 988
    }
    
    notes = "5C 5D 5E 5D 5F 5E 5D 4B 5C"
    for note in notes.split(' '):
        if '5' in note:
            beep.play(scales_5[note[1:]],200)
        elif '4' in note:
            beep.play(scales_5[note[1:]]//2,100)