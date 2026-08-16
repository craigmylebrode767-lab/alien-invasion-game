import array
import math
import pygame


class SoundManager:
    """管理游戏音效：射击、爆炸、飞船被撞（程序内生成，无需音频文件）"""

    RATE = 22050

    def __init__(self):
        pygame.mixer.init(frequency=self.RATE, size=-16,
                          channels=1, buffer=512)
        self.fire = self._tone(880, 0.08)    # 射击：短促高音
        self.explode = self._tone(140, 0.25)  # 爆炸：低沉
        self.hit = self._tone(90, 0.4)        # 飞船被撞：更低沉

    def _tone(self, freq, duration):
        """生成一段带衰减的正弦波音效"""
        n = int(self.RATE * duration)
        data = array.array('h')
        for i in range(n):
            t = i / self.RATE
            data.append(int(30000 * math.sin(2 * math.pi * freq * t)
                            * (1 - t / duration)))
        return pygame.mixer.Sound(buffer=data.tobytes())

    def play_fire(self):
        self.fire.play()

    def play_explode(self):
        self.explode.play()

    def play_hit(self):
        self.hit.play()
