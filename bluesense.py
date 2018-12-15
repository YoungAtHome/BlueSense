##!/usr/bin/env python3
from __future__ import division  # for py2.x compatibility
from time import sleep
from datetime import datetime
from signal import pause
from colorzero import Color
from pisense import SenseHAT, array
from bluedot.btcomm import BluetoothClient
#import skywriter

moving = False

# robot runs the bluedot server
bd_server = 'artipi'
#bd_server = 'BlueZ 5.43'

def movements(imu):
    for reading in imu:
        #print('accel x, y, z={:.3f}, {:.3f}, {:.3f}'.format(imu.accel.x, imu.accel.y, imu.accel.z))
        delta_x = -max(-1, min(1, imu.accel.x))
        delta_y = max(-1, min(1, imu.accel.y))
        delta_z = max(-1, min(1, imu.accel.z))
        #delta_x = int(round(max(-1, min(1, imu.accel.x))))
        #delta_y = int(round(max(-1, min(1, imu.accel.y))))
        print('delta x, y, z={:.3f}, {:.3f}, {:.3f}'.format(delta_x, delta_y, delta_z))
        #if delta_x != 0 or delta_y != 0:
        yield delta_x, delta_y, delta_z
        sleep(1/30)

def arrays(moves):
    a = array(Color('black'))  # blank screen
    x = y = 3
    a[y, x] = Color('white')
    yield a  # initial position
    for dx, dy in moves:
        a[y, x] = Color('black')
        x = max(0, min(7, x + dx))
        y = max(0, min(7, y + dy))
        a[y, x] = Color('white')
        yield a
    a[y, x] = Color('black')
    yield a  # end with a blank display


"""
[operation],[x],[y]\n

operation is either 0, 1 or 2:
 0 released
 1 pressed
 2 pressed position moved

x & y specify the position on the Blue Dot that was pressed, released and/or moved
Positions are values between -1 and +1, with 0 being the centre and 1 being the radius
of the Blue Dot
x is the horizontal position where +1 is far right
y is the horizontal position where +1 is the top
\n represents the ascii new-line character (ASCII character 10)
"""
bd_release = 0
bd_press = 1
bd_hold = 2

ox = 1
oy = 1
oz = 1

pressed = False

#sky_centre = 'center'
direction = {'north': (0, 1), 'east': (1, 0), 'south': (0, -1), 'west': (-1, 0), 'centre': (0, 0)}

def command(operation, bdx, bdy):
  global pressed
  bd_command = '{},{:.3f},{:.3f}\n'
  print('op={} x={:.3f} y={:.3f}'.format(operation, bdx, bdy))
  if operation == bd_release:
    if not pressed: 
      return
    pressed = False
  print('op={} x={:.3f} y={:.3f}'.format(operation, bdx, bdy))
  c.send(bd_command.format(operation, bdx, bdy))


def data_received(data):
    print("recv - {}".format(data))

def move(x, y, z):
  global moving
  global ox, oy, oz
  global pressed
  
  if moving:
    #print('ignore move')
    return
  moving = True
  #print('pressed={}'.format(pressed))
  # act on material differences only
  if abs(abs(ox)-abs(x)) > 0.05 or abs(abs(oy)-abs(y)) > 0.05 or abs(abs(oz)-abs(z)) > 0.05:
    #print('ox={:.3f} oy={:.3f} oz={:.3f}'.format(x, y, z))
    #print(' x={:.3f}  y={:.3f}  z={:.3f}'.format(x, y, z))
    if z >= 0:
      if pressed:
        # send hold
        command(bd_hold, x, y)
      else: #if not pressed:
        pressed = True
        # send press
        command(bd_press, x, y)
    else:
        # z less then 0 so release
        command(bd_release, x, y)
    #print('updating ox, oy, oz')
    ox = x
    oy = y
    oz = z
  #print('moving to False')
  moving = False

#@skywriter.touch()
def touch(position):
  print('Touch!', position)
  bdx, bdy = direction[position]
  if position == sky_centre:
    command(bd_release, bdx, bdy)
  else:
    command(bd_press, bdx, bdy)


try:
  print("Connecting to {}".format(bd_server))
  c = BluetoothClient(bd_server, data_received)
  print("  Connected to {}".format(bd_server))

  with SenseHAT() as hat:
    for m in movements(hat.imu):
      #hat.screen.array = arrays(m)
      move(m[0], m[1], m[2])
      #move(m[0], m[1], m[2])
  #pause()
finally:
  command(bd_release, 0, 0)
  c.disconnect()

