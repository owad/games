import copy
import dataclasses
import logging

import random
from typing import Tuple, List

import pygame
from pygame import Surface

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pygame.init()

MAX_SPEED = 13
GAME_SPEED = 2
CAR_SPEED = 5


@dataclasses.dataclass
class Rect:
    x1: int
    x2: int
    y1: int
    y2: int


class Element:
    x = 0
    y = 0
    respect_borders = False
    image_path: str
    show_explosion = False

    def __init__(self, screen: Surface):
        self.image = pygame.image.load(self.image_path)
        self.screen = screen

    def center_horizontally(self):
        self.x = int(self.screen.get_width() / 2 - self.width / 2)

    def set_position(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def move(self, step: int):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            self.move_up(step)
        if keys[pygame.K_DOWN]:
            self.move_down(step)
        if keys[pygame.K_LEFT]:
            self.move_left(step)
        if keys[pygame.K_RIGHT]:
            self.move_right(step)

    def move_up(self, step: int) -> None:
        y = self.y - step
        if self.respect_borders:
            y = max(0, y)
        self.y = y

    def move_down(self, step: int) -> None:
        y = self.y + step
        if self.respect_borders:
            y = min(self.screen.get_height() - self.height, y)
        self.y = y

    def move_left(self, step: int) -> None:
        x = self.x - step
        if self.respect_borders:
            x = max(0, x)
        self.x = x

    def move_right(self, step: int) -> None:
        x = self.x + step
        if self.respect_borders:
            x = min(self.screen.get_width() - self.width, x)
        self.x = x

    def draw(self):
        explosion_image = pygame.image.load("images/explosion.gif")
        if self.exploded():
            self.screen.blit(explosion_image, (self.x - 60, self.y))
        else:
            self.screen.blit(self.image, (self.x, self.y))

    @property
    def size(self) -> Tuple[int, int]:
        return self.image.get_width(), self.image.get_height()

    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]

    def overlaps_with(self, element: "Element") -> bool:
        element_1_x_position = self.x, self.x + self.width
        element_1_y_position = self.y, self.y + self.height
        element_2_x_position = element.x, element.x + element.width
        element_2_y_position = element.y, element.y + element.height

        x_overlaps = set(range(*element_1_x_position)) & set(range(*element_2_x_position))
        y_overlaps = set(range(*element_1_y_position)) & set(range(*element_2_y_position))

        return x_overlaps and y_overlaps

    def has_left_screen(self) -> bool:
        return self.y - self.height <= 0

    def exploded(self) -> bool:
        return self.show_explosion

    def explode(self):
        self.show_explosion = True

    def unexplode(self):
        self.show_explosion = False


class Car(Element):
    image_paths = [
        # "images/delorean.png",
        "images/dino-car.png",
        # "images/maluch.png",
        # "images/kot.png",
        # "images/car.png",
        # "images/car2.png",
        # "images/car3.png",
        # "images/pickle_rick.png",
    ]
    respect_borders = True
    speed = 5
    bullets = []
    fire_rate = 40
    fire_count = 0

    def __init__(self, **kwargs):
        super(Car, self).__init__(**kwargs)
        self.image = pygame.image.load(self.image_path)
        self.init_car_position()

        self.blast = pygame.image.load("images/rocket_blast.png")

    @property
    def image_path(self):
        return random.choice(self.image_paths)

    def move(self, **kwargs):
        super().move(step=self.speed)

    def init_car_position(self):
        self.center_horizontally()
        self.move_down(self.screen.get_height() - self.height - 20)

    def draw(self):
        super().draw()

        for bullet in self.bullets:
            bullet.draw()
            if bullet.has_left_screen():
                self.bullets.remove(bullet)
                del bullet

    def fire_bullet(self) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not self.exploded():
            if self.fire_count % self.fire_rate == 0:
                self.bullets.append(Bullet(screen=self.screen, car=self))
                self.fire_count = 0
            self.fire_count += 1
        else:
            self.fire_count = 0

    def bullets_hit_opponent(self, game: "Game", opponents: List["OtherCar"]):
        for bullet in self.bullets:
            for opponent in opponents:
                if bullet.overlaps_with(opponent) and not opponent.exploded():
                    opponent.explode()
                    game.score += 2


class Road(Element):
    image_path = "images/road.png"
    respect_borders = False

    def __init__(self, **kwargs):
        super(Road, self).__init__(**kwargs)
        self.center_horizontally()

    def draw(self):
        self.screen.blit(self.image, (self.x, self.y - 800))
        self.screen.blit(self.image, (self.x, self.y - 400))
        self.screen.blit(self.image, (self.x, self.y))
        self.screen.blit(self.image, (self.x, self.y + 400))

        if self.y >= self.screen.get_height():
            self.y = 0


class Obstacle(Element):
    obstacle_images = [
        "images/fuel_tank.png",
    ]

    def __init__(self, **kwargs):
        super(Obstacle, self).__init__(**kwargs)
        self.y = self.get_random_y_position()
        self.x = self.get_random_x_position()

    def get_random_x_position(self) -> int:
        return random.randrange(0, self.screen.get_width() - self.width)

    def get_random_y_position(self) -> int:
        return random.randrange(-1 * self.screen.get_height(), -1 * self.height)

    @property
    def image_path(self):
        return random.choice(self.obstacle_images)

    def draw(self):
        if self.y >= self.screen.get_height():
            self.y = self.get_random_y_position()
            self.x = self.get_random_x_position()
        super().draw()


class OtherCar(Obstacle):
    obstacle_images = [
        "images/car.png",
        "images/car2.png",
        "images/car3.png",
        "images/delorean.png",
        "images/acura.png",
    ]

    def move_down(self, step: int) -> None:
        super().move_down(step=step - 1)

    def draw(self):
        if self.y >= self.screen.get_height():
            self.unexplode()
            self.y = self.get_random_y_position()
            self.x = self.get_random_x_position()
        super().draw()


class Bullet(Obstacle):
    image_path = "images/slime.png"

    def __init__(self, car: Car, **kwargs) -> None:
        super().__init__(**kwargs)
        self.car = car
        self.x = int(car.x + car.width / 2)
        self.y = car.y

    def draw(self):
        self.y -= self.car.speed + 5
        self.screen.blit(self.image, (self.x, self.y - self.car.speed + 3))


class Game:
    running: bool = False
    static_objects: List["Element"]
    game_speed: int = GAME_SPEED
    score: int = 0
    current_speed: int = GAME_SPEED

    def __init__(self, window_width: int = 530, window_height: int = 800):
        self.window_width = window_width
        self.window_height = window_height
        self.static_objects = []

        # setup window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))

        # init player's car
        self.car = Car(screen=self.screen)

        # init static objects
        self.static_objects = [
            Road(screen=self.screen),
            Obstacle(screen=self.screen),
            Obstacle(screen=self.screen),
            Obstacle(screen=self.screen),
            Obstacle(screen=self.screen),
            OtherCar(screen=self.screen),
            OtherCar(screen=self.screen),
            OtherCar(screen=self.screen),
        ]

    def run(self):
        self.running = True

        while self.running:
            self._check_game_closed()
            self._draw_background()

            self._move_static_objects(step=self.game_speed)
            self._draw_statis_objects()

            if self.game_speed > 0:
                self.car.move()

            self.car.draw()

            self.car.fire_bullet()
            self.car.bullets_hit_opponent(self, self.opponents)

            self._draw_score()
            self._fuel_tank_collected()

            if self._reset_pressed():
                self.reset()
                self.score = 0

            if self._opponent_hit():
                self.stop()
                self.car.explode()

            pygame.display.flip()

        pygame.quit()

    def stop(self):
        self.car.speed = 0
        self.game_speed = 0

    def reset(self):
        self.car.speed = CAR_SPEED
        self.car.show_explosion = False
        self.game_speed = GAME_SPEED
        self.car.init_car_position()
        for obstacle in self.obstacles:
            obstacle.x = obstacle.get_random_x_position()
            obstacle.y = obstacle.get_random_y_position()
        for opponent in self.opponents:
            opponent.unexplode()

    @property
    def obstacles(self) -> List[Obstacle]:
        return [obj for obj in self.static_objects if type(obj) == Obstacle]

    @property
    def opponents(self) -> List[OtherCar]:
        return [obj for obj in self.static_objects if type(obj) == OtherCar]

    def _fuel_tank_collected(self) -> bool:
        collected = False
        for obstacle in self.obstacles:
            if self.car.overlaps_with(obstacle):
                obstacle.x = obstacle.get_random_x_position()
                obstacle.y = obstacle.get_random_y_position()
                self.score += 1
                collected = True

                if self.score % 10 == 0:
                    self.game_speed += 1

        return collected

    def _opponent_hit(self) -> bool:
        non_exploded_opponents = [
            o for o in self.opponents if not o.exploded()
        ]
        return any(
            opponent for opponent in non_exploded_opponents if self.car.overlaps_with(opponent)
        )

    @staticmethod
    def _reset_pressed() -> bool:
        return pygame.key.get_pressed()[pygame.K_r]

    def _move_static_objects(self, step: int) -> None:
        for static_object in self.static_objects:
            static_object.move_down(step=step)

    def _draw_statis_objects(self) -> None:
        for static_object in self.static_objects:
            static_object.draw()

    def _check_game_closed(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or getattr(event, "key", None) == pygame.K_ESCAPE:
                self.running = False

    def _draw_background(self):
        self.screen.fill((255, 255, 255))

    def _draw_score(self):
        font = pygame.font.Font("fonts/font.ttf", 32)
        score = font.render(f"SCORE: {str(self.score)}", False, (0, 0, 255))
        self.screen.blit(score, (30, 0))

    def _increase_speed(self) -> None:
        self.speed = min(MAX_SPEED, self.game_speed + 1)


if __name__ == "__main__":
    Game().run()
