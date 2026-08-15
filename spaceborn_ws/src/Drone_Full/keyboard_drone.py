#!/usr/bin/env python3
"""
Keyboard teleop for the drone. Publishes geometry_msgs/Twist to
/drone/cmd_vel, which drone_hover_controller.py reads to:
    - climb / descend           (W / S)
    - tilt forward / backward   (I / K)   -> moves drone forward/back
    - tilt left / right         (J / L)   -> moves drone left/right
    - yaw left / right          (A / D)   -> accepted but NOT modeled
                                              (no prop reaction torque in
                                              your current Gazebo plugin
                                              setup, so this currently
                                              has no effect)
    - level off / reset         (SPACE)
    - quit                      (Q or Ctrl-C)

Run this in its own terminal (needs a real TTY, not an IDE "run" panel):
    python3 drone_keyboard_teleop.py
"""

import sys
import termios
import tty
import select

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

INSTRUCTIONS = """
Drone Keyboard Teleop
----------------------
  W / S   : climb / descend
  I / K   : tilt forward / backward (move forward/back)
  J / L   : tilt left / right (move left/right)
  A / D   : yaw left / right   (NOT modeled yet - no effect currently)
  SPACE   : level off (zero all commands, just hover)
  Q       : quit

Hold a key to keep moving; commands decay back toward hover if you
stop pressing keys (release = level + hold altitude).
----------------------
"""


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('drone_keyboard_teleop')
        self.pub = self.create_publisher(Twist, '/drone/cmd_vel', 10)

        self.lin_x = 0.0   # forward/back tilt command, -1..1
        self.lin_y = 0.0   # left/right tilt command, -1..1
        self.lin_z = 0.0   # throttle offset, -1..1
        self.ang_z = 0.0   # yaw, accepted but unused downstream

        self.step = 0.15        # how much each keypress nudges the command
        self.decay = 0.85       # commands decay toward 0 each tick if no key pressed

        self.timer = self.create_timer(0.05, self.publish_cmd)  # 20 Hz

    def publish_cmd(self):
        msg = Twist()
        msg.linear.x = self.lin_x
        msg.linear.y = self.lin_y
        msg.linear.z = self.lin_z
        msg.angular.z = self.ang_z
        self.pub.publish(msg)

        # gentle auto-decay so it doesn't keep climbing/tilting forever
        # if a key gets "stuck" or you stop pressing
        self.lin_x *= self.decay
        self.lin_y *= self.decay
        self.ang_z *= self.decay
        # NOTE: lin_z (throttle) decays toward 0 too -> means "no extra
        # throttle", not "fall out of the sky" -> base hover thrust still
        # applies in the controller regardless of this offset.
        self.lin_z *= self.decay

    def clamp(self, v):
        return max(-1.0, min(1.0, v))

    def handle_key(self, key):
        if key == 'w':
            self.lin_z = self.clamp(self.lin_z + self.step)
        elif key == 's':
            self.lin_z = self.clamp(self.lin_z - self.step)
        elif key == 'i':
            self.lin_x = self.clamp(self.lin_x + self.step)
        elif key == 'k':
            self.lin_x = self.clamp(self.lin_x - self.step)
        elif key == 'j':
            self.lin_y = self.clamp(self.lin_y + self.step)
        elif key == 'l':
            self.lin_y = self.clamp(self.lin_y - self.step)
        elif key == 'a':
            self.ang_z = self.clamp(self.ang_z + self.step)
        elif key == 'd':
            self.ang_z = self.clamp(self.ang_z - self.step)
        elif key == ' ':
            self.lin_x = self.lin_y = self.ang_z = 0.0
            # NOTE: deliberately NOT zeroing lin_z here, so SPACE levels
            # attitude without suddenly cutting climb throttle.


def get_key(settings, timeout=0.1):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def main():
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()
    node = KeyboardTeleop()
    print(INSTRUCTIONS)

    try:
        while rclpy.ok():
            key = get_key(settings)
            if key:
                if key.lower() == 'q':
                    break
                node.handle_key(key.lower())
            rclpy.spin_once(node, timeout_sec=0.0)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()