# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>

import pygame
from pygame.sprite import AbstractGroup, Group
import sys
import random

WIDTH = 800
HEIGHT = 800

TILE_SIZE = 20


class World:
    def __init__(self):
        self.tiles = Group()
        self.boundaries = Group()
        self.food = Group()

        self.setup_tiles()
        self.snake = Snake((TILE_SIZE, TILE_SIZE), self.food, self.boundaries)

        self.MAX_FOOD = 3
        self.is_game_over = False
        self.food_types = [
            {
                "color": "red",
                "prob": 0.5,
                "score": 1,
            },
            {
                "color": "yellow",
                "prob": 0.3,
                "score": 2,
            },
            {
                "color": "orange",
                "prob": 0.1,
                "score": 5,
            },
            {
                "color": "cyan",
                "prob": 0.05,
                "score": 10,
            }
        ]

    @property
    def score(self):
        return self.snake.score

    @property
    def food_count(self):
        return len(self.food.sprites())

    def reset_world(self):
        self.__init__()

    def create_node(self, i, j, color):
        return Node((i * TILE_SIZE, j * TILE_SIZE), color)

    def setup_tiles(self):
        rows = HEIGHT // TILE_SIZE
        cols = WIDTH // TILE_SIZE
        for i in range(rows):
            for j in range(cols):
                if i in [0, rows - 1] or j in [0, cols - 1]:
                    tile = self.create_node(i, j, "darkgray")
                    tile.is_boundary = True
                    self.boundaries.add(tile)
                else:
                    tile = Node((i * TILE_SIZE, j * TILE_SIZE), "black")

                self.tiles.add(tile)

    def check_game_over(self):
        if self.score == -1:
            self.is_game_over = True

    def spawn_food(self):
        if not self.food_count == self.MAX_FOOD:
            probs = [food["prob"] for food in self.food_types]
            food_type = random.choices(self.food_types, probs)[0]
            node = random.choice(self.tiles.sprites())
            if not node.is_food and not node.is_boundary:
                node.score = food_type["score"]
                node.color = food_type["color"]
                node.is_food = True
                self.food.add(node)

    def game_over(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            self.reset_world()

    def update(self):
        self.tiles.update()
        self.food.update()
        self.snake.update()
        self.check_game_over()


class UI:
    def __init__(self):
        self.score = 0
        self.display = pygame.display.get_surface()
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 25)

    @property
    def score_text(self):
        return "Score: " + str(self.score)

    def game_over(self):
        text = self.font.render("You lose! Press R to retry!", True, "white")
        text_rect = text.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        self.display.blit(text, (text_rect.x, text_rect.y))

    def update_score(self, value):
        self.score = value

    def update(self):
        self.display.blit(self.font.render(self.score_text, True, "white"), (0, 0))


class Snake:
    def __init__(self, pos: tuple, food, boundaries):
        self.head = Node(pos, "forestgreen")
        self.body = [self.head]
        self.score = 0
        self.food = food
        self.boundaries = boundaries
        self.direction = pygame.math.Vector2(1, 0)

    def process_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            if not self.direction.x == 1:
                self.direction.x = -1
                self.direction.y = 0
        elif keys[pygame.K_RIGHT]:
            if not self.direction.x == -1:
                self.direction.x = 1
                self.direction.y = 0
        elif keys[pygame.K_UP]:
            if not self.direction.y == 1:
                self.direction.y = -1
                self.direction.x = 0
        elif keys[pygame.K_DOWN]:
            if not self.direction.y == -1:
                self.direction.y = 1
                self.direction.x = 0

    def new(self):
        pos = self.body[-1].rect.x, self.body[-1].rect.x
        self.body.append(Node(pos, "green"))

    def check_collision(self):
        t = None
        for tile in self.food.sprites():
            if self.head.rect.colliderect(tile.rect):
                t = tile
                self.score += t.score
                self.new()
                break

        for tile in self.body:
            if not self.head == tile:
                if self.head.rect.colliderect(tile):
                    self.score = -1

        for tile in self.boundaries.sprites():
            if self.head.rect.colliderect(tile):
                self.score = -1

        if t:
            t.is_food = False
            t.score = 0
            t.color = "black"
            self.food.remove(t)

    def move_body(self):
        last_position = self.head.rect.copy()
        for node in self.body:
            aux = node.rect.copy()
            node.rect = last_position
            last_position = aux

    def update(self):
        self.process_input()
        self.check_collision()
        self.move_body()
        if self.score >= 0:
            self.head.rect.x += TILE_SIZE * self.direction.x
            self.head.rect.y += TILE_SIZE * self.direction.y
        for node in self.body:
            node.update()


class Node(pygame.sprite.Sprite):
    def __init__(self, pos: tuple, color: str, *groups: AbstractGroup):
        super().__init__(*groups)
        self.image = pygame.surface.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.color = color
        self.score = 0
        self.is_food = False
        self.is_boundary = False

    def update(self):
        display = pygame.display.get_surface()
        #display.blit(self.image, (self.rect.x, self.rect.y))
        pygame.draw.rect(display, self.color, self.rect)
        pygame.draw.rect(display, "gray18", self.rect, width=1)


class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 10

        self.world = World()
        self.ui = UI()

    def update(self):
        self.window.fill("black")
        if self.world.is_game_over:
            self.ui.game_over()
            self.world.game_over()
        else:
            self.world.update()
            self.ui.update()
            self.ui.update_score(self.world.score)
        self.clock.tick(self.fps)
        pygame.display.update()

    def run(self):
        spawn_food = pygame.event.custom_type()
        pygame.time.set_timer(spawn_food, 1000)
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == spawn_food:
                    self.world.spawn_food()

            self.update()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
