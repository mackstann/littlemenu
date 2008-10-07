#!/usr/bin/env python

# this file is based on test.py from simple-python-gui.
# Copyright (c) 2008 Canio Massimo "Keebus" Tristano
# Copyright (c) 2008 Nick Welch <mack@incise.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os, random, time, sys
import pygame
from pygame import font, joystick, event

import gui

def init():
    pygame.init()

    global sticks
    sticks = map(pygame.joystick.Joystick, range(pygame.joystick.get_count()))
    for s in sticks:
        s.init()

    global screen
    highest_res = sorted(pygame.display.list_modes())[-1]
    screen = pygame.display.set_mode(highest_res, pygame.FULLSCREEN)

    reload(gui)

    gui.defaultListBoxStyle = {}
    gui.defaultListBoxStyle['font'] = pygame.font.Font(None, font_size)
    gui.defaultListBoxStyle['font'].set_bold(True)
    gui.defaultListBoxStyle['antialias'] = True
    gui.defaultListBoxStyle['item-height'] = int(font_size * 1.2)
    gui.defaultListBoxStyle['bg-color'] = bg
    gui.defaultListBoxStyle['bg-color-over'] = (200,0,0) #irrelevant
    gui.defaultListBoxStyle['bg-color-selected'] = fg
    gui.defaultListBoxStyle['font-color'] = fg
    gui.defaultListBoxStyle['font-color-selected'] = bg
    gui.defaultListBoxStyle['padding'] = 0
    gui.defaultListBoxStyle['autosize'] = False
    gui.defaultListBoxStyle['border-width'] = 0

    global clock
    clock = pygame.time.Clock()

    pygame.mouse.set_visible(0)
    pygame.mouse.set_pos((0, 0))

    global desktop
    desktop = gui.Desktop()

    global listbox
    listbox = gui.ListBox(position=(0,1), size=desktop.size, parent=desktop)

    if menu_stack:
        listbox.items = menus[menu_stack[-1]]




def shutdown():
    global sticks, screen, clock
    sticks = screen = clock = None
    pygame.quit()

def createDialogWindow(widget):
    win = Window(
        position = center((0,0), desktop.size, (200,100)),
        size = (200,100),
        parent = desktop,
        dialog = True
    )
    Label(
        text = "This is a dialog window. \nClick the close button to proceed",
        parent = win,
        position = (5,30)
    )
	
def rungame(filename):
    pass

class Back(object):
    def __str__(self):
        return '< Back'
    def __call__(self):
        pop_menu()

class Exit(object):
    def __str__(self):
        return '[ Exit ]'
    def __call__(self):
        shutdown()
        raise SystemExit

class Game(object):
    def __init__(self, fullpath, command):
        self.display = os.path.basename(os.path.splitext(fullpath)[0])
        self.fullpath = fullpath
        self.command = command
    def __str__(self):
        return self.display
    def __call__(self):
        shutdown()
        os.system(self.command + ' ' + shellquote(self.fullpath))
        init()

class SubMenu(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name
    def __call__(self):
        push_menu(self.name)

def directory(command, path, extensions):
    return [
        Game(os.path.join(path, fn), command)
        for fn in sorted(os.listdir(path), cmp=lambda a, b: cmp(a.lower(), b.lower()))
        if os.path.isfile(os.path.join(path, fn))
        and filter(fn.endswith, extensions)
    ]

def shellquote(s):
    return "\\'".join("'" + p + "'" for p in s.split("'"))

def switch_to_list(name):
    global listbox, desired_scroll_num_per_sec
    listbox.items = menus[name]
    desired_scroll_num_per_sec = max(len(listbox.items) / 4, 20)
    while listbox.selectedIndex > 0:
        listbox.moveUp()
    listbox.needsRefresh = True

def push_menu(name):
    menu_stack.append(name)
    switch_to_list(name)

def pop_menu():
    menu_stack.pop()
    switch_to_list(menu_stack[-1])

menus = {
    'Emulators': [SubMenu('NES'), SubMenu('SNES'), Exit()],
    'NES':  [Back()] + directory('fceux', os.path.expanduser('~/roms/nes'), ['.nes']) + [Back()],
    'SNES': [Back()] + directory('zsnes', os.path.expanduser('~/roms/snes'), ['.fig', '.smc', '.zip']) + [Back()],
}
main = 'Emulators'

# likely will need to change these (L2 & R2 on a PSX controller via a USB
# adapter)
up_button = 4
down_button = 5

# for generating random bg/fg colors
#bg = (
#    random.randint(0, 255),
#    random.randint(0, 255),
#    random.randint(0, 255),
#)
#fg = (
#    random.randint(0, 255),
#    random.randint(0, 255),
#    random.randint(0, 255),
#)
#print bg, fg

# ok, i found a combo i like for now
bg, fg = (100, 91, 214), (183, 241, 222)

font_size = 24

sticks = []
screen = None
clock = None
desktop = None
listbox = None
menu_stack = []
desired_scroll_num_per_sec = 1

init()

push_menu(main)

lastmove = 0
lastcheck = time.time()
tomovedown = 0
tomoveup = 0
while 1:
    clock.tick()
    
    startover = False
    gui.events = pygame.event.get()
    for e in gui.events:
        # any button other than the scroll buttons will execute a menu item
        if e.type == pygame.JOYBUTTONDOWN and e.button not in (down_button, up_button):
            item = listbox.items[listbox.selectedIndex]
            item()
            if isinstance(item, Game):
                startover = True
                break
    if startover:
        continue

    now = time.time()
    elapsed = now - lastcheck

    for stick in sticks:
        axisvalue = stick.get_axis(1)
        if abs(axisvalue) > 0.7 and now - lastmove > 0.15:
            if axisvalue > 0:
                tomovedown += 1
            else:
                tomoveup += 1
            lastmove = now

        if stick.get_button(up_button):
            tomoveup += desired_scroll_num_per_sec * elapsed
            tomovedown = 0

        if stick.get_button(down_button):
            tomovedown += desired_scroll_num_per_sec * elapsed
            tomoveup = 0

        for i in range(int(tomovedown)):
            listbox.moveDown()

        for i in range(int(tomoveup)):
            listbox.moveUp()

        tomovedown %= 1
        tomoveup %= 1

    lastcheck = now
    
    #UPDATE YOUR LOGIC BEFORE UPDATING THE GUI
    
    #The desktop should be the last thing you update (for performance reasons)
    #First let the gui know events occurred
    
    desktop.update()
    desktop.draw()
    pygame.display.flip()

shutdown()

