import sys
from pathlib import Path

# 确保从任意目录直接运行时都能导入 classicprogram 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from time import sleep

import pygame

from classicprogram.game.settings import Settings
from classicprogram.game.game_stats import GameStats
from classicprogram.game.scoreboard import Scoreboard
from classicprogram.game.ship import Ship
from classicprogram.game.bullet import Bullet
from classicprogram.game.alien import Alien
from classicprogram.game.button import Button
from classicprogram.game.sound import SoundManager


class AlienInvasion:

    # ====== 初始化和主循环 ======

    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()

        self.clock = pygame.time.Clock()
        self.running = True

        self.settings = Settings()

        if self.settings.fullscreen:
            self.screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (
                    self.settings.screen_width,
                    self.settings.screen_height
                )
            )

        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        pygame.display.set_caption('Alien Invasion')

        # 创建一个用于存储游戏统计信息的实例
        self.stats = GameStats(self)
        self.scoreboard = Scoreboard(self)

        # 游戏元素：飞船、子弹、外星人
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        # 游戏启动后处于非活动状态
        self.game_active = False

        # 创建 Play 按钮
        self.play_button = Button(self, "Play")

        # 初始化音效
        self.sound = SoundManager()

    def run_game(self):
        """开始游戏的主循环"""
        while self.running:
            self._check_events()

            if self.game_active:
                self.ship.update()
                self._update_bullets()
                self._check_bullet_alien_collisions()
                self._update_aliens()

            self._update_screen()
            self.clock.tick(60)

        pygame.quit()


    # ====== 屏幕绘制 ======

    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        self.screen.fill(self.settings.bg_color)

        # 绘制子弹
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()

        # 绘制飞船
        self.ship.blitme()

        # 绘制外星人
        self.aliens.draw(self.screen)

        # 显示得分
        self.scoreboard.show_score()

        # 如果游戏处于非活动状态，就绘制 Play 按钮
        if not self.game_active:
            self.play_button.draw_button()

        pygame.display.flip()


    # ====== 事件响应 ======

    def _check_events(self):
        """侦听并响应键盘、鼠标等事件"""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)

            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_keydown_events(self, event):
        """响应按下键盘按键"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True

        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True

        elif event.key == pygame.K_UP:
            self.ship.moving_up = True

        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = True

        elif event.key == pygame.K_q:
            self.running = False

        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

        elif event.key == pygame.K_p:
            self._start_game()

    def _check_keyup_events(self, event):
        """响应释放键盘按键"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False

        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

        elif event.key == pygame.K_UP:
            self.ship.moving_up = False

        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = False

    def _check_play_button(self, mouse_pos):
        """在玩家单击 Play 按钮时开始游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)

        if button_clicked:
            self._start_game()


    # ====== 游戏状态控制 ======

    def _start_game(self):
        """开始一局新的游戏"""
        if not self.game_active:
            # 重置游戏的统计信息
            self.stats.reset_stats()

            self.scoreboard.prep_score()
            self.scoreboard.prep_level()
            self.scoreboard.prep_ships()

            self.game_active = True

            # 清空外星人列表和子弹列表
            self.bullets.empty()
            self.aliens.empty()

            # 创建一个新的外星舰队
            self._create_fleet()

            # 将飞船放在屏幕底部的中央
            self.ship.center_ship()

            # 隐藏光标
            pygame.mouse.set_visible(False)

            # 还原游戏设置
            self.settings.initialize_dynamic_settings()

    def _ship_hit(self):
        """响应飞船和外星人的碰撞"""
        if self.stats.ships_left > 0:

            # 将 ships_left 减 1
            self.stats.ships_left -= 1
            self.scoreboard.prep_ships()

            # 播放飞船被击中的音效
            self.sound.play_hit()

            # 清空外星人列表和子弹列表
            self.bullets.empty()
            self.aliens.empty()

            # 创建一个新的外星舰队
            self._create_fleet()

            # 将飞船放在屏幕底部的中央
            self.ship.center_ship()

            # 暂停
            sleep(0.5)

        else:
            # 游戏结束
            self.game_active = False
            pygame.mouse.set_visible(True)


    # ====== 子弹管理 ======

    def _fire_bullet(self):
        """创建一颗子弹，并将其加入编组 bullets"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

            # 播放发射子弹的音效
            self.sound.play_fire()

    def _update_bullets(self):
        """更新子弹的位置并删除已消失的子弹"""

        # 更新子弹的位置
        self.bullets.update()

        # 删除已消失的子弹
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

    def _check_bullet_alien_collisions(self):
        """检查子弹是否击中了外星人"""
        collisions = pygame.sprite.groupcollide(
            self.bullets,
            self.aliens,
            True,
            True
        )

        if collisions:
            # 播放爆炸音效
            self.sound.play_explode()

            # 根据消灭的外星人数量增加得分
            for aliens in collisions.values():
                self.stats.score += (
                    self.settings.alien_points *
                    len(aliens)
                )

                self.scoreboard.prep_score()
                self.scoreboard.check_high_score()

        # 如果所有外星人都被消灭，创建下一波外星人
        if not self.aliens:
            # 删除现有的子弹
            self.bullets.empty()

            # 创建一个新的外星舰队
            self._create_fleet()

            # 提高游戏速度
            self.settings.increase_speed()

            # 提高等级
            self.stats.level += 1
            self.scoreboard.prep_level()


    # ====== 外星人管理 ======

    def _create_fleet(self):
        """创建一个外星舰队"""

        # 创建一个外星人，用它的尺寸来计算舰队布局
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        # 从左上角开始放置外星人
        current_x = alien_width
        current_y = alien_height

        # 不断添加外星人，直到没有空间为止
        while current_y < (
            self.settings.screen_height - 4 * alien_height
        ):
            while current_x < (
                self.settings.screen_width - 2 * alien_width
            ):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width

            # 添加一行外星人后，重置 x 值并增加 y 值
            current_x = alien_width
            current_y += 2 * alien_height

    def _create_alien(self, x_position, y_position):
        """创建一个外星人并将其放在当前行中"""
        new_alien = Alien(self)

        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position

        self.aliens.add(new_alien)

    def _update_aliens(self):
        """检查外星人边缘、更新外星人并处理碰撞"""

        # 检查外星人是否到达屏幕边缘
        self._check_fleet_edges()

        # 更新所有外星人的位置
        self.aliens.update()

        # 检测外星人和飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # 检查是否有外星人到达屏幕底部
        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        """检查外星人是否到达屏幕边缘"""
        for alien in self.aliens.sprites():

            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """将整个外星舰队向下移动，并改变它们的方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed

        # 改变舰队的水平移动方向
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        """检查是否有外星人到达屏幕的下边缘"""
        for alien in self.aliens.sprites():

            if alien.rect.bottom >= self.settings.screen_height:
                # 像飞船被撞到一样进行处理
                self._ship_hit()
                break


if __name__ == '__main__':
    # 创建游戏实例并运行游戏
    ai = AlienInvasion()
    ai.run_game()