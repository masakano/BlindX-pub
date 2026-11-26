# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import logging
import random

class Login():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available_names = [
            'Alice', 'Bob', 'Charol', 'Charile', 'Dave', 'Eve', 'Ellen', 'Frank', 'Isac', 'IVan', 
            'Justin', 'Marvin', 'Matilda', 'Oscar', 'Peggy', 'Steve', 'Trent', 'Trudy', 'Walter', 'Zoe' 
        ]
        self.active_names = []
        self.guest_count = 0

    async def login_async(self):
        if self.available_names:
            name = random.choice(self.available_names)
        else:
            # 用意した名前を使い切ったら、連番のゲスト名を払い出す
            self.guest_count += 1
            name = f'Guest{self.guest_count}'
        await self.connect_async(name)
        return name

    # 再接続 (Flet の on_connect / on_disconnect) からも呼ばれるため、
    # 二重登録や、すでに取り除かれた名前の削除で例外にならないようにする
    async def connect_async(self, name):
        self.logger.info(f'connect {name}')
        if name not in self.active_names:
            self.active_names.append(name)
        if name in self.available_names:
            self.available_names.remove(name)

    async def disconnect_async(self, name):
        if name in self.active_names:
            self.active_names.remove(name)
        if name not in self.available_names:
            self.available_names.append(name)
        self.logger.info(f'disconnect {name}')

