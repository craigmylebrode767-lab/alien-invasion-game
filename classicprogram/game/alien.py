import pygame
from pathlib import Path
from pygame.sprite import Sprite

class Alien(Sprite):
    """表示单个外星人的类"""

    def __init__(self,ai_game):
        """初始化外星人并设置其初始位置"""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings

        #加载外星人图像并设置其rect属性
        self.image = pygame.image.load(Path(__file__).resolve().parent.parent / 'images' / 'alien.bmp')
        # 原图较大时按比例缩放到合适的外星人尺寸，保证舰队能正常排布
        scale = 60 / self.image.get_height()
        self.image = pygame.transform.scale(
            self.image,
            (int(self.image.get_width() * scale), 60)
        )
        self.rect = self.image.get_rect()

        #每个外星人初始位置都在屏幕的左上角附近
        self.rect.x = self.rect.width
        self.rect.y = self.rect.height

        #存储外星人的精确位置
        self.x = float(self.rect.x)


    def update(self):
        """向右移动外星人"""
        self.x += self.settings.alien_speed * self.settings.fleet_direction
        self.rect.x = self.x

    def check_edges(self):
        """如果外星⼈位于屏幕边缘，就返回 True"""
        screen_rect = self.screen.get_rect()
        return ((self.rect.right >= screen_rect.right)
                or
                (self.rect.left <= 0)
                )

