from time import sleep

import pygame

from game.settings import Settings
from game.game_stats import GameStats
from game.scoreboard import Scoreboard
from game.ship import Ship
from game.bullet import Bullet
from game.alien import Alien
from game.button import Button
from game.sound import SoundManager


class AlienInvasion:
    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()

        self.clock = pygame.time.Clock()
        self.running = True
        self.settings = Settings()
        if self.settings.fullscreen:
            self.screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(
                (self.settings.screen_width,
                 self.settings.screen_height))
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption('Alien Invasion')

        # 创建⼀个⽤于存储游戏统计信息的实例
        self.stats = GameStats(self)
        self.scoreboard = Scoreboard(self)

        #游戏元素：飞船、子弹、外星人
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        # 游戏启动后处于活动状态
        self.game_active = False

        #创建Play按钮
        self.play_button = Button(self, "Play")

        #初始化音效
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

    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        self.screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)

        # 显⽰得分
        self.scoreboard.show_score()

        #如果游戏处于非活动状态，就绘制Play按钮
        if not self.game_active:
            self.play_button.draw_button()

        pygame.display.flip()

    def _check_events(self):
        """侦听响应键盘和鼠标事件"""
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

    def _check_play_button(self, mouse_pos):
        """在玩家单击Play按钮时开始游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked:
            self._start_game()

    def _start_game(self):
        if not self.game_active:
            # 重置游戏的统计信息
            self.stats.reset_stats()
            self.scoreboard.prep_score()
            self.scoreboard.prep_level()
            self.scoreboard.prep_ships()
            self.game_active = True

            # 清空外星⼈列表和⼦弹列表
            self.bullets.empty()
            self.aliens.empty()
            # 创建⼀个新的外星舰队，并将⻜船放在屏幕底部的中央
            self._create_fleet()
            self.ship.center_ship()

            # 隐藏光标
            pygame.mouse.set_visible(False)

            #还原游戏设置
            self.settings.initialize_dynamic_settings()

    def _check_keydown_events(self, event):
        """响应按下"""
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
        """响应释放"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_UP:
            self.ship.moving_up = False
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = False

    def _fire_bullet(self):
        """创建⼀颗⼦弹，并将其加⼊编组 bullets """
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
            self.sound.play_fire()

    def _update_bullets(self):
        """更新⼦弹的位置并删除已消失的⼦弹"""
        # 更新⼦弹的位置
        self.bullets.update()
        # 删除已消失的⼦弹
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

    def _check_bullet_alien_collisions(self):
        #检查是否有子弹击中了外星人
        #如果是，就删除相应的子弹和外星人
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)

        if collisions:
            self.sound.play_explode()
            for aliens in collisions.values():
                self.stats.score += (self.settings.alien_points*
                                     len(aliens))
                self.scoreboard.prep_score()
                self.scoreboard.check_high_score()

        if not self.aliens:
            # 删除现有的⼦弹并创建⼀个新的外星舰队
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # 提⾼等级
            self.stats.level += 1
            self.scoreboard.prep_level()

    def _create_fleet(self):
        """创建一个外星舰队"""
        #创建一个外星人，再不断添加，直到没有空间添加外星人为止
        #外星人的间距为外星人的宽度和外星人的高度
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height -
                           4 * alien_height):
            while current_x < (self.settings.screen_width -
                               2 * alien_width):
                self._create_alien(current_x,current_y)
                current_x += 2 * alien_width

            #添加一行外星人后，重置x值并递增y值
            current_x = alien_width
            current_y += 2 * alien_height

    def _create_alien(self, x_position, y_position):
        """创建⼀个外星⼈并将其放在当前⾏中"""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)

    def _update_aliens(self):
        """检查是否有外星⼈位于屏幕边缘，并更新整个外星舰队的位置"""
        self._check_fleet_edges()
        self.aliens.update()

        #检测外星人和飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # 检查是否有外星⼈到达了屏幕的下边缘
        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        """在有外星⼈到达边缘时采取相应的措施"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """将整个外星舰队向下移动，并改变它们的⽅向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        """检查是否有外星⼈到达了屏幕的下边缘"""
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                # 像⻜船被撞到⼀样进⾏处理
                self._ship_hit()
                break

    def _ship_hit(self):
        """响应⻜船和外星⼈的碰撞"""
        if self.stats.ships_left > 0:
            # 将 ships_left 减 1
            self.stats.ships_left -= 1
            self.scoreboard.prep_ships()
            self.sound.play_hit()

            # 清空外星⼈列表和⼦弹列表
            self.bullets.empty()
            self.aliens.empty()

            # 创建⼀个新的外星舰队，并将⻜船放在屏幕底部的中央
            self._create_fleet()
            self.ship.center_ship()

            # 暂停
            sleep(0.5)
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)


if __name__ == '__main__':
    #创建游戏实例并运行游戏
    ai = AlienInvasion()
    ai.run_game()
