from pyMeow import *
from data import Offsets, Info
from urllib.request import urlopen
from orjson import loads
from pyMeow import open_process, get_module, draw_circle, get_color, r_float
from utils import send_key
from ctypes import windll

import win32api
from script_class import UserScript
from data import VK_CODES
from scripts_manager import Colors
from time import time
import time
from math import sqrt
import keyboard
import win32con
from win32api import GetCursorPos, mouse_event, GetSystemMetrics
from dearpygui.dearpygui import add_checkbox, tree_node, add_combo


class Script(UserScript):
    def __init__(self):
        super().__init__()
        self.script_name = 'Testing grounds Ezreal by Czechu'
        self.script_prefix = 'Testing grounds Ezreal by Czechu'
        self.just_executed = False
        self.prio = 'Nearest Enemy'  
        self.use_q = True
        self.use_w = True

    def set_prio(self, _, data):
        self.prio = data
        self.VakScript_set_setting('prio', data)
        print(data)

    def toggle_use_q(self, _, value):
        self.use_q = value
        print(f"Use Q: {value}")

    def toggle_use_w(self, _, value):
        self.use_w = value
        print(f"Use W: {value}")

    def VakScript_draw_menu(self):
        with tree_node(label=f'{self.script_name}', default_open=True):
            add_checkbox(label=f'Enable {self.script_name}',default_value=self.VakScript_get_setting('enabled'),callback=self.VakScript_start_process)
            add_combo(label='Target Prio', width=150, items=['lowest hp', 'Nearest Enemy'],default_value=self.VakScript_get_setting('prio'),callback=lambda _, data: self.set_prio(_, data))
            add_checkbox(label='Use Q', default_value=self.use_q, callback=self.toggle_use_q)
            add_checkbox(label='Use W', default_value=self.use_w, callback=self.toggle_use_w)

    def info(self):
        url = "https://127.0.0.1:2999/liveclientdata/activeplayer"
        response = urlopen(url)
        if response.getcode() == 200:
            data = response.read().decode('utf-8')
            data_dict = loads(data)
            playerlevel = data_dict['level']
            return playerlevel

    def main(self, attr_reader, draw, world, local_player, champions, wards, minions, turrets, game_time):
        global prio
        prio = self.prio
        view_proj_matrix = world.get_view_proj_matrix()
        world_to_screen = world.world_to_screen
        player = attr_reader.read_player(local_player)
        enemy_targets = []
        for champion in champions:
            enemy = attr_reader.read_enemy(champion.pointer)
            enemy_targets.append(enemy)
        lowest_hp_enemy = self.lowest_hp(player, enemy_targets)
        if prio == 'Nearest Enemy':
            closest_enemy = self.findClosestEnemy(player, enemy_targets)
        else:
            print(prio)
            closest_enemy = self.findlowEnemy(player, enemy_targets)
        if lowest_hp_enemy is not None:
            print(f'lowest hp: {lowest_hp_enemy.health}')
        else:
            print('No enemy found within range.')
        if player:
            if self.isOrbwalking():
                own_pos = world_to_screen(view_proj_matrix, player.x, player.z, player.y)
                draw_font(1, f'{"Orbwalk active"}', own_pos[0] + 30, own_pos[1] + 20, 20, 2, new_color(255, 203, 0, 255))
                print("Orbwalking is active.")

                if self.use_w and self.spellWIsAvailable(local_player, attr_reader, game_time):
                    closest_enemy = self.findClosestEnemy(player, enemy_targets)
                    if closest_enemy is not None:
                        self.useW(world, closest_enemy, attr_reader, player)
                    else:
                        print("No enemy found for useW")
                else:
                    print("W spell is not available or not enabled.")

                if self.use_q and self.spellQIsAvailable(local_player, attr_reader, game_time):
                    closest_enemy = self.findClosestEnemy(player, enemy_targets)
                    if closest_enemy is not None:
                        if self.is_Q_colliding_with_minion(player, closest_enemy, minions):
                            print("Q would collide with a minion.")
                        else:
                            self.useQ(world, closest_enemy, attr_reader, player)
                            print("Q would not collide with a minion.")
                    else:
                        print("No enemy found for useQ")
                else:
                    print("Q spell is not available or not enabled.")

    def isOrbwalking(self):
        space_key = "space"
        return keyboard.is_pressed(space_key)

    def findlowEnemy(self, player, enemies):
        print("lowest hp")
        closest_enemy = None
        min_health = float('inf')
        max_range = 1400
        for enemy in enemies:
            distance = sqrt((player.x - enemy.x) ** 2 + (player.y - enemy.y) ** 2 + (player.z - enemy.z) ** 2)
            health = enemy.health
            if distance <= max_range and health <= min_health and enemy.alive:
                min_health = health
                closest_enemy = enemy
        print("Target acquired")
        return closest_enemy

    def findClosestEnemy(self, player, enemies):
        closest_enemy = None
        min_distance = float('inf')
        max_range = 1400
        for enemy in enemies:
            distance = sqrt((player.x - enemy.x) ** 2 + (player.y - enemy.y) ** 2 + (player.z - enemy.z) ** 2)
            if distance < min_distance and enemy.alive and distance <= max_range:
                min_distance = distance
                closest_enemy = enemy
        print("target aquired")
        return closest_enemy
    
    def lowest_hp(self, player, enemies):
        ultimate_range = 5000
        lowest_hp = float('inf')
        lowest_hp_enemy = None
        for enemy in enemies:
            distance = sqrt((player.x - enemy.x) ** 2 + (player.y - enemy.y) ** 2 + (player.z - enemy.z) ** 2)
            print(f'{enemy.name} at {distance}')
            if enemy.health < lowest_hp and distance <= ultimate_range:
                lowest_hp = enemy.health
                lowest_hp_enemy = enemy
        return lowest_hp_enemy

    def QSpellInfo(self):
        q_cost = [28, 31, 34, 37, 40] 
        q_cast_time = 0.25  
        q_range = 1200  
        q_width = 120  
        q_speed = 2000  

        return q_cost, q_cast_time, q_range, q_width, q_speed

    def defQRange(self, player, enemy):
        q_info = self.QSpellInfo()
        q_range = q_info[2]  
        distance = sqrt((player.x - enemy.x) ** 2 + (player.y - enemy.y) ** 2 + (player.z - enemy.z) ** 2)
        return distance <= q_range
    
    def distance_point_to_line(self, line_point1, line_point2, point):
        x1, y1, z1 = line_point1
        x2, y2, z2 = line_point2
        x, y, z = point
        AB = (x2 - x1, y2 - y1, z2 - z1)
        AC = (x - x1, y - y1, z - z1)
        cross_product = (AB[1] * AC[2]) - (AB[2] * AC[1]), (AB[2] * AC[0]) - (AB[0] * AC[2]), (AB[0] * AC[1]) - (AB[1] * AC[0])
        if all(coord == 0 for coord in cross_product):
            return 0  
        else:
            distance = sqrt(sum(coord ** 2 for coord in cross_product)) / sqrt(sum(coord ** 2 for coord in AB))
            return distance
    
    def is_Q_colliding_with_minion(self, player, enemy, minions):
        q_info = self.QSpellInfo()
        q_range = q_info[2] 
        q_width = q_info[3]  
        q_speed = q_info[4] 
        q_cast_time = q_info[1] 

        displacement_speed = q_speed / 1000  

        displacement_distance = displacement_speed * q_cast_time

        for minion in minions:
            distance_to_line = self.distance_point_to_line((player.x, player.y, player.z), (enemy.x, enemy.y, enemy.z), (minion.x, minion.y, minion.z))
            if distance_to_line <= q_width / 2 and distance_to_line <= q_range + displacement_distance:
                return True  
        return False  

    def defWRange(self, player, enemy):
        w_range = 1150  
        distance = sqrt((player.x - enemy.x) ** 2 + (player.y - enemy.y) ** 2 + (player.z - enemy.z) ** 2)
        return distance <= w_range

    def useQ(self, world, enemy, attr_reader, player):
        mouse_pos_initial = GetCursorPos()
        updated_enemy = attr_reader.read_enemy(enemy.pointer)
        time.sleep(0.1)
        updated_updated_enemy = attr_reader.read_enemy(enemy.pointer)
        if updated_enemy.health <= 0 or updated_updated_enemy.visible == False:
            return
        if not self.defQRange(player, updated_enemy):
            print("Enemy is out of Q range.")
            return
        pos_new = world.world_to_screen(world.get_view_proj_matrix(), updated_updated_enemy.x+3*(updated_updated_enemy.x-updated_enemy.x) , updated_updated_enemy.z+3*(updated_updated_enemy.z-updated_enemy.z), updated_updated_enemy.y+3*(updated_updated_enemy.y-updated_enemy.y))
        x, y = mouse_pos_initial
        screen_width = GetSystemMetrics(0)
        screen_height = GetSystemMetrics(1)
        pos_new_x = max(0, min(pos_new[0], screen_width))
        pos_new_y = max(0, min(pos_new[1], screen_height))
        mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(pos_new_x / screen_width * 65535.0), int(pos_new_y / screen_height * 65535.0))
        keyboard.press_and_release('q')
        print("Q casted!")
        time.sleep(0.01)
        mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(x / screen_width * 65535.0), int(y / screen_height * 65535.0))
        global qready
        qready = 0
        time.sleep(1.5)


    def useW(self, world, enemy, attr_reader, player):
        mouse_pos_initial = GetCursorPos()
        updated_enemy = attr_reader.read_enemy(enemy.pointer)
        time.sleep(0.1)
        updated_updated_enemy = attr_reader.read_enemy(enemy.pointer)
        if updated_enemy.health <= 0 or updated_updated_enemy.visible == False:
            return
        if not self.defWRange(player, updated_enemy):
            print("Enemy is out of W range.")
            return
        pos_new = world.world_to_screen(world.get_view_proj_matrix(), updated_updated_enemy.x+3*(updated_updated_enemy.x-updated_enemy.x) , updated_updated_enemy.z+3*(updated_updated_enemy.z-updated_enemy.z), updated_updated_enemy.y+3*(updated_updated_enemy.y-updated_enemy.y))
        x, y = mouse_pos_initial
        screen_width = GetSystemMetrics(0)
        screen_height = GetSystemMetrics(1)
        pos_new_x = max(0, min(pos_new[0], screen_width))
        pos_new_y = max(0, min(pos_new[1], screen_height))
        mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(pos_new_x / screen_width * 65535.0), int(pos_new_y / screen_height * 65535.0))
        keyboard.press_and_release('w')
        print("W casted!")
        time.sleep(0.01)
        mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(x / screen_width * 65535.0), int(y / screen_height * 65535.0))
        global wready
        wready = 0
        time.sleep(1.5)

    def spellQIsAvailable(self, local_player, attr_reader, game_time):
        try:
            cooldown_Q = attr_reader.read_spells(local_player)[0]['cooldown']
            return cooldown_Q < game_time
        except Exception as q:
            print("Error in spellQIsAvailable:", q)
            return False
        
    def spellWIsAvailable(self, local_player, attr_reader, game_time):
        try:
            cooldown_W = attr_reader.read_spells(local_player)[1]['cooldown']
            return cooldown_W < game_time
        except Exception as w:
            print("Error in spellQIsAvailable:", w)
            return False