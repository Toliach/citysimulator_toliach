import arcade
import math
import time
from pathlib import Path

# Константы
SCREEN_WIDTH = 940
SCREEN_HEIGHT = 640
GRID_SIZE = 8
CELL_SIZE = 64
GRID_OFFSET_X = 64
GRID_OFFSET_Y = 64
UI_PANEL_WIDTH = 300

# Типы построек с путями к спрайтам
BUILDING_TYPES = {
    1: {
        "name": "Деревянный дом",
        "width": 1,
        "height": 1,
        "cost": 5,
        "population": 2,
        "sprite": "wooden_house_small.png",
        "color": arcade.color.BROWN
    },
    2: {
        "name": "Многоквартирный дом",
        "width": 2,
        "height": 2,
        "cost": 20,
        "population": 10,
        "sprite": "apartament_small.png",
        "color": arcade.color.GRAY
    },
    3: {
        "name": "Завод",
        "width": 2,
        "height": 2,
        "cost": 30,
        "population": 0,
        "income": 10,
        "sprite": "factory_small.png",
        "color": arcade.color.RED
    }
}


class Building(arcade.Sprite):
    def __init__(self, building_type, grid_x, grid_y, scale=1.0):
        self.type = building_type
        self.data = BUILDING_TYPES[building_type]
        
        # Пытаемся загрузить спрайт
        sprite_path = self.data["sprite"]
        if Path(sprite_path).exists():
            try:
                super().__init__(sprite_path, scale=scale)
            except:
                # Если не удалось загрузить, создаём цветной квадрат
                super().__init__()
                self.color = self.data["color"]
                self.texture = self.create_simple_texture(CELL_SIZE * scale)
        else:
            # Создаём цветной квадрат, если спрайт не найден
            super().__init__()
            self.color = self.data["color"]
            self.texture = self.create_simple_texture(CELL_SIZE * scale)
        
        # Устанавливаем позицию
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.width_cells = self.data["width"]
        self.height_cells = self.data["height"]
        self.last_income_time = time.time()
        
        # Вычисляем центр спрайта
        center_x = GRID_OFFSET_X + grid_x * CELL_SIZE + (self.width_cells * CELL_SIZE) / 2
        center_y = GRID_OFFSET_Y + grid_y * CELL_SIZE + (self.height_cells * CELL_SIZE) / 2
        self.center_x = center_x
        self.center_y = center_y
        
        # Устанавливаем размеры для спрайта
        self.width = self.width_cells * CELL_SIZE
        self.height = self.height_cells * CELL_SIZE
        
        # Создаем текст с информацией о здании
        self.info_text = arcade.Text(
            self.data["name"].split()[0],
            center_x,
            center_y - 15,
            arcade.color.WHITE,
            10,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # Если это завод, создаем дополнительный текст
        if self.type == 3:
            self.income_text = arcade.Text(
                "$",
                center_x,
                center_y + 15,
                arcade.color.GOLD,
                14,
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
        else:
            self.income_text = None
    
    def create_simple_texture(self, size):
        """Создаёт простую текстуру с цветом здания"""
        # Создаём текстуру с помощью draw_commands
        texture = arcade.Texture.create_empty(f"building_{self.type}", (int(size), int(size)))
        return texture
    
    def get_grid_coverage(self):
        """Возвращает список занятых клеток"""
        occupied = []
        for dx in range(self.width_cells):
            for dy in range(self.height_cells):
                occupied.append((self.grid_x + dx, self.grid_y + dy))
        return occupied
    
    def draw_info(self):
        """Рисует информацию о здании"""
        self.info_text.draw()
        if self.income_text:
            self.income_text.draw()


class CityBuildingGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Симулятор Собянина")
        
        # Игровые переменные
        self.money = 100
        self.population = 0
        
        # Спрайтовые списки
        self.building_list = arcade.SpriteList()
        self.ghost_building_sprite = None
        
        # Игровое поле (для проверки занятости клеток)
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Состояние игры
        self.selected_building = None
        self.ghost_building_data = None
        self.show_shop = False
        
        # Время для дохода от заводов
        self.last_income_check = time.time()
        self.income_timer = 0
        
        # Цвета
        self.grid_color = arcade.color.LIGHT_GRAY
        self.grid_line_color = arcade.color.GRAY
        self.ui_bg_color = arcade.color.DARK_SLATE_GRAY
        self.ui_text_color = arcade.color.WHITE
        self.button_color = arcade.color.BLUE_GRAY
        self.button_hover_color = arcade.color.LIGHT_BLUE
        
        # Загружаем текстуры для кнопок магазина
        self.shop_textures = {}
        self.load_textures()
        
        # Кнопки магазина
        self.shop_buttons = []
        self.create_shop_buttons()
        
        # Таймер для анимации
        self.animation_timer = 0
        
    def load_textures(self):
        """Загружает текстуры для зданий"""
        for building_id, data in BUILDING_TYPES.items():
            sprite_path = data["sprite"]
            if Path(sprite_path).exists():
                try:
                    self.shop_textures[building_id] = arcade.load_texture(sprite_path)
                except:
                    # Если не удалось загрузить, создаём простую текстуру
                    self.shop_textures[building_id] = None
            else:
                self.shop_textures[building_id] = None
    
    def create_shop_buttons(self):
        button_width = 250
        button_height = 80
        start_x = SCREEN_WIDTH - UI_PANEL_WIDTH + 25
        start_y = SCREEN_HEIGHT - 100
        
        for i, (building_id, data) in enumerate(BUILDING_TYPES.items()):
            button = {
                "id": building_id,
                "x": start_x,
                "y": start_y - i * (button_height + 15),
                "width": button_width,
                "height": button_height,
                "text": f"{data['name']} \n Стоимость: {data['cost']} \n Население: +{data.get('population', 0)}",
                "multiline": True,
                "hover": False
            }
            if building_id == 3:
                button["text"] = f"{data['name']} \n Стоимость: {data['cost']} \n Доход: +{data.get('income', 0)}$/10сек"
            
            self.shop_buttons.append(button)
    
    def on_draw(self):
        self.clear()
        
        # Рисуем фон с градиентом
        self.draw_background()
        
        # Рисуем игровое поле
        self.draw_grid()
        
        # Рисуем постройки
        self.building_list.draw()

        for building in self.building_list:
            building.draw_info()
            # Рисуем призрачное здание (если есть)
        if self.ghost_building_data:
            data = BUILDING_TYPES[self.ghost_building_data["type"]]
            grid_x = self.ghost_building_data["grid_x"]
            grid_y = self.ghost_building_data["grid_y"]

            can_place = self.can_place_building(
                grid_x, grid_y,
                data["width"], data["height"]
            )

            color = (100, 255, 100, 150) if can_place else (255, 100, 100, 150)

            w = data["width"] * CELL_SIZE * 0.9
            h = data["height"] * CELL_SIZE * 0.9

            cx = GRID_OFFSET_X + grid_x * CELL_SIZE + (data["width"] * CELL_SIZE)
            cy = GRID_OFFSET_Y + grid_y * CELL_SIZE + (data["height"] * CELL_SIZE)
            self.ghost_building_sprite.center_x = cx
            self.ghost_building_sprite.center_y = cy

            arcade.draw_rect_filled(
                arcade.rect.XYWH(cx - w / 2, cy - h / 2, w, h),
                color
            )
            # Рисуем контур
            outline_color = arcade.color.GREEN if can_place else arcade.color.RED
        
        # Рисуем UI панель
        self.draw_ui_panel()
        
        # Рисуем магазин (если открыт)
        if self.show_shop:
            self.draw_shop()
    
    def draw_background(self):
        """Рисует фон с градиентом"""
        # Небо
        for i in range(SCREEN_HEIGHT // 2, SCREEN_HEIGHT):
            color_value = int(100 + 155 * (i - SCREEN_HEIGHT // 2) / (SCREEN_HEIGHT // 2))
            arcade.draw_lrbt_rectangle_filled(
                0, SCREEN_WIDTH, i, i + 1,
                (color_value, color_value, 255)
            )
        
        # Земля
        for i in range(0, SCREEN_HEIGHT // 2):
            color_value = int(50 + 100 * i / (SCREEN_HEIGHT // 2))
            arcade.draw_lrbt_rectangle_filled(
                0, SCREEN_WIDTH, i, i + 1,
                (0, color_value, 0)
            )
    
    def draw_grid(self):
        """Рисует игровую сетку"""
        # Рисуем клетки с альтернирующими цветами
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                color = arcade.color.LIGHT_GREEN if (x + y) % 2 == 0 else arcade.color.DARK_GREEN
                arcade.draw_lrbt_rectangle_filled(
                    GRID_OFFSET_X + x * CELL_SIZE,
                    GRID_OFFSET_X + (x + 1) * CELL_SIZE,
                    GRID_OFFSET_Y + y * CELL_SIZE,
                    GRID_OFFSET_Y + (y + 1) * CELL_SIZE,
                    color
                )
        
        # Рисуем линии сетки
        for x in range(GRID_SIZE + 1):
            line_x = GRID_OFFSET_X + x * CELL_SIZE
            arcade.draw_line(line_x, GRID_OFFSET_Y, line_x, 
                           GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE, 
                           self.grid_line_color, 2)
        
        for y in range(GRID_SIZE + 1):
            line_y = GRID_OFFSET_Y + y * CELL_SIZE
            arcade.draw_line(GRID_OFFSET_X, line_y, 
                           GRID_OFFSET_X + GRID_SIZE * CELL_SIZE, line_y, 
                           self.grid_line_color, 2)
        
        # Рисуем номера строк и столбцов
        for i in range(GRID_SIZE):
            # Номера столбцов
            arcade.draw_text(
                str(i + 1),
                GRID_OFFSET_X + i * CELL_SIZE + CELL_SIZE / 2,
                GRID_OFFSET_Y - 25,
                arcade.color.WHITE,
                14,
                anchor_x="center",
                bold=True
            )
            # Номера строк
            arcade.draw_text(
                chr(65 + i),
                GRID_OFFSET_X - 25,
                GRID_OFFSET_Y + i * CELL_SIZE + CELL_SIZE / 2,
                arcade.color.WHITE,
                14,
                anchor_y="center",
                bold=True
            )
        
        # Заголовок игрового поля
        arcade.draw_text(
            "А здесь построем люля-кебаб",
            GRID_OFFSET_X + (GRID_SIZE * CELL_SIZE) / 2,
            GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 20,
            arcade.color.WHITE,
            18,
            anchor_x="center",
            bold=True
        )
    
    def draw_ui_panel(self):
        """Рисует панель интерфейса"""
        # Фон UI панели с тенью
        arcade.draw_lrbt_rectangle_filled(
            SCREEN_WIDTH - UI_PANEL_WIDTH, 
            SCREEN_WIDTH, 
            0,
            SCREEN_HEIGHT, 
            self.ui_bg_color
        )
        
        # Верхняя часть панели
        arcade.draw_lrbt_rectangle_filled(
            SCREEN_WIDTH - UI_PANEL_WIDTH, 
            SCREEN_WIDTH, 
            SCREEN_HEIGHT - 60, 
            SCREEN_HEIGHT, 
            arcade.color.DARK_BLUE
        )
        
        # Заголовок
        arcade.draw_text(
            "Мухосранск",
            SCREEN_WIDTH - UI_PANEL_WIDTH + 10,
            SCREEN_HEIGHT - 40,
            arcade.color.GOLD,
            22,
            width=UI_PANEL_WIDTH - 20,
            align="center",
            bold=True
        )
        
        # Панель ресурсов
        panel_x = SCREEN_WIDTH - UI_PANEL_WIDTH + 150
        panel_y = SCREEN_HEIGHT - 120
        panel_width = UI_PANEL_WIDTH - 40
        panel_height = 120
    
    # Создаем прямоугольник с использованием явных параметров
        arcade.draw_rect_filled(arcade.rect.XYWH(panel_x, panel_y, panel_width, panel_height), arcade.color.DARK_GRAY)
        
        arcade.draw_text(
            f"{self.money} $",
            SCREEN_WIDTH - UI_PANEL_WIDTH + 80,
            SCREEN_HEIGHT - 100,
            arcade.color.WHITE,
            28,
            bold=True
        )
        
        # Население с иконкой
        arcade.draw_text(
            "👥",
            SCREEN_WIDTH - UI_PANEL_WIDTH + 40,
            SCREEN_HEIGHT - 150,
            arcade.color.LIGHT_BLUE,
            30
        )
        
        arcade.draw_text(
            f"{self.population} человеков",
            SCREEN_WIDTH - UI_PANEL_WIDTH + 80,
            SCREEN_HEIGHT - 150,
            arcade.color.WHITE,
            28,
            bold=True
        )
        
        # Кнопка магазина с иконкой
        shop_button_color = self.button_hover_color if self.show_shop else self.button_color
        center_x = SCREEN_WIDTH - UI_PANEL_WIDTH-25 + UI_PANEL_WIDTH / 2
        center_y = SCREEN_HEIGHT - 220
        width = 200
        height = 60
    
    # Прямоугольник для кнопки (с центром в center_x, center_y)
        rect_x = center_x+100 - width/2
        rect_y = center_y+25 - height/2
        arcade.draw_rect_filled(arcade.rect.XYWH(rect_x, rect_y, width, height), shop_button_color)
        arcade.draw_rect_outline(arcade.rect.XYWH(rect_x, rect_y, width, height), arcade.color.WHITE, 2)
        
        arcade.draw_text(
            "МАГАЗ",
            center_x,
            center_y,
            self.ui_text_color,
            22,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        
        # Статистика
        arcade.draw_text(
            "Статистика:",
            SCREEN_WIDTH - UI_PANEL_WIDTH + 20,
            SCREEN_HEIGHT - 300,
            arcade.color.LIGHT_YELLOW,
            18,
            bold=True
        )
        
        arcade.draw_text(
            f"Построек: {len(self.building_list)}",
            SCREEN_WIDTH - UI_PANEL_WIDTH + 30,
            SCREEN_HEIGHT - 330,
            self.ui_text_color,
            16
        )
    
    def draw_shop(self):
        """Рисует магазин построек"""
        # Полупрозрачный фон
        arcade.draw_rect_filled(arcade.rect.XYWH(SCREEN_WIDTH - UI_PANEL_WIDTH +150, 400, UI_PANEL_WIDTH, SCREEN_HEIGHT - 100), (0, 0, 0, 200))
        
        # Заголовок магазина
        arcade.draw_text(
            "МАГАЗ",
            SCREEN_WIDTH - UI_PANEL_WIDTH + UI_PANEL_WIDTH / 2,
            SCREEN_HEIGHT - 40,
            arcade.color.GOLD,
            24,
            anchor_x="center",
            bold=True
        )
        
        # Кнопки построек
        for button in self.shop_buttons:
            # Фон кнопки
            color = self.button_hover_color if button["hover"] else self.button_color
            center_x = button["x"] + button["width"] / 2
            center_y = button["y"]
            width = button["width"]
            height = button["height"]
            
            arcade.draw_rect_filled(arcade.rect.XYWH(center_x - width/2 + 120, center_y - height/2 + 35, width, height), color)

            arcade.draw_rect_outline(arcade.rect.XYWH(center_x - width/2 + 120, center_y - height/2 + 35, width, height), arcade.color.WHITE, 2)
            
            # Миниатюра здания (цветной квадрат)
            building_data = BUILDING_TYPES[button["id"]]
            arcade.draw_rect_filled(arcade.rect.XYWH(button["x"] + 40 - 20, button["y"] - 20, 40, 40), building_data["color"])
            
            # Текст кнопки
            arcade.draw_text(
                button["text"],
                button["x"] + 80,
                button["y"],
                self.ui_text_color,
                14,
                anchor_y="center",
                width=button["width"] - 90,
                align="left",
                multiline=True
            )
    
    def on_mouse_motion(self, x, y, dx, dy):
        # Обновляем состояние кнопок магазина (наведение)
        if self.show_shop:
            for button in self.shop_buttons:
                button_x_center = button["x"] + button["width"] / 2
                button_y_center = button["y"]
                button["hover"] = (
                    abs(x - button_x_center) < button["width"] / 2 and
                    abs(y - button_y_center) < button["height"] / 2
                )
        
        # Обновляем позицию призрачного здания
        if self.selected_building:
            # Преобразуем координаты мыши в координаты сетки
            grid_x = math.floor((x - GRID_OFFSET_X) / CELL_SIZE)
            grid_y = math.floor((y - GRID_OFFSET_Y) / CELL_SIZE)
            
            # Проверяем границы
            data = BUILDING_TYPES[self.selected_building]
            grid_x = max(0, min(grid_x, GRID_SIZE - data["width"]))
            grid_y = max(0, min(grid_y, GRID_SIZE - data["height"]))
            
            # Создаём или обновляем призрачное здание
            self.ghost_building_data = {
                "type": self.selected_building,
                "grid_x": grid_x,
                "grid_y": grid_y
            }
            
            # Создаём спрайт призрачного здания
            if not self.ghost_building_sprite:
                self.ghost_building_sprite = Building(
                    self.selected_building, 
                    grid_x, 
                    grid_y,
                    scale=0.95
                )
                self.ghost_building_sprite.alpha = 150
            else:
                # Обновляем позицию
                center_x = GRID_OFFSET_X + grid_x * CELL_SIZE + (data["width"] * CELL_SIZE) / 2
                center_y = GRID_OFFSET_Y + grid_y * CELL_SIZE + (data["height"] * CELL_SIZE) / 2
                self.mouse_x = center_x
                self.gmouse_y = center_y
                self.ghost_building_sprite.grid_x = grid_x
                self.ghost_building_sprite.grid_y = grid_y
    
    def on_mouse_press(self, x, y, button, modifiers):
        # Если нажата левая кнопка мыши
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Проверяем, нажали ли на кнопку магазина
            shop_button_x = SCREEN_WIDTH - UI_PANEL_WIDTH + UI_PANEL_WIDTH / 2
            if (shop_button_x - 100 <= x <= shop_button_x + 100 and
                SCREEN_HEIGHT - 250 <= y <= SCREEN_HEIGHT - 190):
                self.show_shop = not self.show_shop
                if self.show_shop:
                    self.selected_building = None
                    self.ghost_building_sprite = None
                    self.ghost_building_data = None
                return
            
            # Если открыт магазин, проверяем кнопки построек
            if self.show_shop:
                for shop_button in self.shop_buttons:
                    button_x_center = shop_button["x"] + shop_button["width"] / 2
                    button_y_center = shop_button["y"]
                    if (abs(x - button_x_center) < shop_button["width"] / 2 and
                        abs(y - button_y_center) < shop_button["height"] / 2):
                        
                        # Выбираем постройку
                        self.selected_building = shop_button["id"]
                        self.show_shop = False
                        return
            
            # Если выбрана постройка, пытаемся разместить её
            if self.selected_building and self.ghost_building_data:
                data = BUILDING_TYPES[self.selected_building]
                grid_x = self.ghost_building_data["grid_x"]
                grid_y = self.ghost_building_data["grid_y"]
                
                if self.can_place_building(grid_x, grid_y, data["width"], data["height"]):
                    if self.money >= data["cost"]:
                        # Создаём новое здание
                        building = Building(self.selected_building, grid_x, grid_y)
                        self.building_list.append(building)
                        
                        # Занимаем клетки
                        for dx in range(data["width"]):
                            for dy in range(data["height"]):
                                if 0 <= grid_x + dx < GRID_SIZE and 0 <= grid_y + dy < GRID_SIZE:
                                    self.grid[grid_x + dx][grid_y + dy] = building
                        
                        # Вычитаем деньги и добавляем население
                        self.money -= data["cost"]
                        self.population += data.get("population", 0)
                        
                        # Сбрасываем выбор
                        self.selected_building = None
                        self.ghost_building_sprite = None
                        self.ghost_building_data = None
    
    def can_place_building(self, grid_x, grid_y, width, height):
        """Проверяет, можно ли разместить здание"""
        # Проверяем границы
        if (grid_x < 0 or grid_y < 0 or 
            grid_x + width > GRID_SIZE or 
            grid_y + height > GRID_SIZE):
            return False
        
        # Проверяем, свободны ли клетки
        for dx in range(width):
            for dy in range(height):
                if self.grid[grid_x + dx][grid_y + dy] is not None:
                    return False
        
        return True
    
    def on_update(self, delta_time):
        """Обновление игровой логики"""
        # Обновляем таймер анимации
        self.animation_timer += delta_time
        
        # Обновляем призрачное здание (пульсация)
        if self.ghost_building_sprite:
            # Пульсирующая прозрачность
            pulse = math.sin(self.animation_timer * 5) * 50 + 150
            self.ghost_building_sprite.alpha = max(100, min(200, pulse))
        
        # Обновляем таймер дохода
        self.income_timer += delta_time
        if self.income_timer >= 10:
            self.income_timer = 0

            total_income = 0
            for building in self.building_list:
                if building.type == 3:  # Завод
                    total_income += building.data["income"]

            if total_income > 0:
                self.money += total_income
    
    def on_key_press(self, key, modifiers):
        """Обработка нажатий клавиш"""
        # ESC для отмены выбора постройки
        if key == arcade.key.ESCAPE:
            self.selected_building = None
            self.ghost_building_sprite = None
            self.ghost_building_data = None
        
        # F1 для справки
        elif key == arcade.key.F1:
            self.show_shop = not self.show_shop
        
        # Тестовые клавиши (для разработки)
        elif key == arcade.key.P:
            self.money += 100
        elif key == arcade.key.O:
            self.population += 10


def main():
    """Главная функция"""
    window = CityBuildingGame()
    
    # Настройка окна
    window.set_update_rate(1/60)  # 60 FPS
    
    # Запуск игры
    arcade.run()


if __name__ == "__main__":
    main()