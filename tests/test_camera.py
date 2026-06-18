import pygame

from settings import SCREEN_H, SCREEN_W
from systems.camera import Camera


def test_initial_offset_is_zero():
    camera = Camera()
    assert camera.offset.x == 0
    assert camera.offset.y == 0


def test_follow_at_screen_center_gives_zero_offset():
    camera = Camera()
    camera.follow(pygame.Vector2(SCREEN_W // 2, SCREEN_H // 2))
    assert camera.offset.x == 0
    assert camera.offset.y == 0


def test_follow_offset_formula():
    camera = Camera()
    camera.follow(pygame.Vector2(0, 0))
    assert camera.offset.x == -(SCREEN_W // 2)
    assert camera.offset.y == -(SCREEN_H // 2)


def test_follow_updates_offset_on_repeated_calls():
    camera = Camera()
    camera.follow(pygame.Vector2(100, 200))
    camera.follow(pygame.Vector2(500, 600))
    assert camera.offset.x == 500 - SCREEN_W // 2
    assert camera.offset.y == 600 - SCREEN_H // 2
