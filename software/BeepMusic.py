import Beep
import utime


class BeepMusic:
    beep = None
    scales = {
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
        'B': 988,
        'W': 40000 # 停顿Wait
    }
    
    def __init__(self,beep):
        self.beep = beep
    
    def __decode(self,note):
        freq_times = 1
        if note[0] == '5':
            freq_times = 1
        elif note[0] == '6':
            freq_times = 2
        elif note[0] == '4':
            freq_times = 0.5
        
        duration_ms = 250
        if note[-1] == '4':
            duration_ms = duration_ms
        elif note [-1] == '8':
            duration_ms = duration_ms * 2
        elif note [-1] == '2':
            duration_ms = duration_ms // 2
        elif note [-1] == '6':
            duration_ms = duration_ms + duration_ms // 2
        
        freq = int(self.scales[note[1:-1]] * freq_times)
        
        return freq, duration_ms
    
    def play(self,notes):
        for note in notes.split(' '):
            freq, d = self.__decode(note)
            self.beep.play(freq, d)
            utime.sleep_ms(10)
            

if __name__ == "__main__":
    notes = "5C8 5D8 5E8 5D8 5F8 5E8 5D4 4B4 5C8 5W2 5G8 5F8 5E8 5D8 5D8 5E4 5D4 5G8"
    beepmusic = BeepMusic(Beep.Beep(28))
    beepmusic.play(notes)

            
            
            
            
            
            