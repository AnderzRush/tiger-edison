#!/usr/bin/env python

# Author: Andres Rubio Chavez <andres.rubio.chavez@gmail.com>

import mraa
import time
import tank_config as CFG
import multiprocessing as mp

def __run_thread(self, thread_obj, function, args=None):
    __stop_thread(thread_obj)
    thread_obj = mp.Process(target=fuction, args=args)
    thread_obj.start()

def __stop_thread(self, thread_obj):
    if thread_obj.is_alive():
        thread_obj.terminate()
        thread_obj.join()

class Tank:
    '''Main object representing the tank'''
    def __init__(self):
        self.propulsion = Propulsion()
        self.turret = Turret()
        self.radio = Radio()
        self.vision = Vision()
        self.lights = Lights()
        self.commander = Commander()

    def fire(self):
        pass

class Propulsion:
    '''Object representing the track pair block'''
    def __init__(self):
        self.left_track = Track(
                fwd_pin=CFG.TRACK_LEFT_FWD_PWM_PIN,
                rev_pin=CFG.TRACK_LEFT_REV_PWM_PIN)
        self.right_track = Track(
                fwd_pin=CFG.TRACK_RIGHT_FWD_PWM_PIN,
                rev_pin=CFG.TRACK_RIGHT_REV_PWM_PIN)

class Track:
    '''Object representing a tank track'''
    def __init__(self, fwd_pin, rev_pin):
        self.fwd = mraa.Pwm(fwd_pin)
        self.rev = mraa.Pwm(rev_pin)
        self.fwd.write(0.0)
        self.rev.write(0.0)
        self.fwd.enable(False)
        self.rev.enable(False)
        self.fwd.period_us(CFG.PWM_PERIOD_US)
        self.rev.period_us(CFG.PWM_PERIOD_US)

    def stop(self):
        self.fwd.write(0.0)
        self.rev.write(0.0)
        self.enable(False)
        self.enable(False)

    def move(self, speed=0.0, direction="FWD"):
        if speed >= 0.0 and speed <= 1.0:
            if direction == "FWD":
                self.rev.write(0.0)
                self.rev.enable(False)
                self.fwd.write(speed)
                self.fwd.enable(True)
                return 0
            elif direction == "REV":
                self.fwd.write(0.0)
                self.fwd.enable(False)
                self.rev.write(speed)
                self.rev.enable(True)
                return 0
            else:
                return 1
        else:
            return 1

    def __change_period_us(self, period_us):
        self.fwd.period_us(period_us)
        self.rev.period_us(period_us)

class Turret:
    '''Object representing the tank turret'''
    def __init__(self):
        self.muzzle = Muzzle()
        self.cannon = Cannon()
        self.mech = TurretEngine()

class TurretEngine:
    '''Object representing the turret mechanics'''
    def __init__(self):
        self.left = mraa.Gpio(CFG.TURRET_LEFT_GPIO_PIN)
        self.left.dir(mraa.DIR_OUT)
        self.left.write(0)
        self.right = mraa.Gpio(CFG.TURRET_RIGHT_GPIO_PIN)
        self.right.dir(mraa.DIR_OUT)
        self.right.write(0)
        self.thread = mp.Process(target=None)

    def move_left(self):
        self.right.write(0)
        self.left.write(1)

    def move_right(self):
        self.left.write(0)
        self.right.write(1)

    def stop(self):
        self.left.write(0)
        self.right.write(0)

class Muzzle:
    '''Object representing the tank muzzle'''
    def __init__(self):
        self.up = mraa.Gpio(CFG.MUZZLE_UP_GPIO_PIN)
        self.up.dir(mraa.DIR_OUT)
        self.up.write(0)
        self.down = mraa.Gpio(CFG.MUZZLE_DOWN_GPIO_PIN)
        self.down.dir(mraa.DIR_OUT)
        self.down.write(0)

    def move_up(self):
        self.down.write(0)
        self.up.write(1)

    def move_down(self):
        self.up.write(0)
        self.down(1)

    def stop(self):
        self.up.write(0)
        self.down.write(0)

class Cannon:
    '''Object representing the tank cannon'''
    def __init__(self, callback=None):
        if callback == None:
            callback = self.__default_callback
        self.callback = callback
        self.fire = mraa.Gpio(CFG.CANNON_FIRE_GPIO_PIN)
        self.fire.dir(mraa.DIR_OUT)
        self.fire.write(0)
        self.feedback = mraa.Gpio(CFG.CANNON_SWITCH_GPIO_PIN)
        self.feedback.dir(mraa.DIR_IN)
        self.feedback.isr(mraa.EDGE_RISING, self.__isr_routine, self.feedback)

    def __default_callback(self):
        self.abort()

    def __isr_routine(self):
        self.callback()
        self.feedback.isrExit()

    def fire(self):
        self.fire.write(1)

    def abort(self):
        self.fire.write(0)

class Lights:
    '''Object representing the tank lights'''
    def __init__(self):
        self.headlights = mraa.Gpio(CFG.HEADLIGHTS_GPIO_PIN)
        self.headlights.dir(mraa.DIR_OUT)
        self.headlights.write(0)
        self.stoplight_left = mraa.Gpio(CFG.STOPLIGHT_LEFT_GPIO_PIN)
        self.stoplight_left.dir(mraa.DIR_OUT)
        self.stoplight_left.write(0)
        self.stoplight_right = mraa.Gpio(CFG.STOPLIGHT_RIGHT_GPIO_PIN)
        self.stoplight_right.dir(mraa.DIR_OUT)
        self.stoplight_right.write(0)
        self.lights_thread = mp.Process(target=None)

    def head_on(self):
        self.headlights.write(1)

    def head_off(self):
        self.headlights.write(0)

    def stop_off(self):
        self.stoplight_left.write(0)
        self.stoplight_right.write(0)

    def stop_on(self):
        self.stoplight_left.write(1)
        self.stoplight_right.write(1)

    def intermittents_on(self, mode):
        __run_thread(thread_obj=self.lights_thread, function=__intermittents, args=(mode,))

    def intermittents_off(self):
        __stop_thread(thread_obj=self.lights_thread)
        self.stop_off()

    def __intermittents(self, mode='BOTH'):
        condition = True
        while condition:
            if mode == 'BOTH':
                self.stoplight_left.write(1)
                self.stoplight_right.write(1)
            elif mode == 'LEFT':
                self.stoplight_right.write(0)
                self.stoplight_left.write(1)
            elif mode == 'RIGHT':
                self.stoplight_left.write(0)
                self.stoplight_right.write(1)
            else:
                condition = False
            time.sleep(1)
            self.stop_off()
            time.sleep(1)
        return

class Radio:
    '''Object representing the tank radiocontroller'''
    pass

class Vision:
    '''Object representing the tank vision'''
    pass

class Commander:
    '''Object representing the tank commander'''
    pass

def main():
    # Magic
    tiger = Tank()
    value = 0.0
    direction = "FWD"
    counter = 0
    while counter < 1000:
        if value < 0.5:
            value = value + 0.01
            tiger.propulsion.left_track.move(value, direction)
            tiger.propulsion.right_track.move(value, direction)
            counter += 1
            time.sleep(0.05)
        else:
            value = 0.0
            if direction == "FWD":
                direction = "REV"
            else:
                direction = "FWD"

if __name__ == "__main__":
    main()
