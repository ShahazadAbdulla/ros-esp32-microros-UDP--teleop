import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32 # Using Int32 for communication
import sys
import select
import termios
import tty

# Define the key mappings (W=1, A=2, S=3, D=4, Space=0)
key_map = {
    'W': 1,
    'A': 2,
    'S': 3,
    'D': 4,
    ' ': 0  # Space key maps to 0 (STOP)
}

# User interface message
msg = """
---------------------------
      ESP32 WASD CONTROL
---------------------------
    W : Send 1 (Forward)
 A : Send 2 (Left)
 S : Send 3 (Backward)
 D : Send 4 (Right)

 SPACE : Send 0 (Stop)

 CTRL-C to quit
---------------------------
"""

def getKey(settings):
    """Gets a single key press without needing Enter (Linux/macOS)."""
    if sys.platform == 'win32':
        print("Error: Windows keyboard capture not implemented.")
        return None
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    key = ''
    if rlist:
        key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

class WasdCommandPublisher(Node):
    """Node to publish WASD/Space commands as integers."""
    def __init__(self):
        super().__init__('wasd_command_publisher_node')
        # Publish Int32 messages to the '/wasd_command' topic
        self.publisher_ = self.create_publisher(Int32, 'wasd_command', 10)
        self.settings = termios.tcgetattr(sys.stdin)
        self.get_logger().info(f"'{self.get_name()}' started.")
        self.get_logger().info("Publishing integer commands to topic: /wasd_command")
        print(msg)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.last_sent_command = None # Optional: track last sent to potentially avoid repeats

    def timer_callback(self):
        """Called periodically to check for key presses."""
        key = getKey(self.settings)
        if key:
            # Use upper case for WASD, keep space as is for lookup
            lookup_key = key.upper() if key != ' ' else ' '

            if lookup_key in key_map:
                command_int = key_map[lookup_key]
                # Optional: Only publish if the command is different from the last one sent
                # if command_int != self.last_sent_command:
                int_msg = Int32()
                int_msg.data = command_int
                self.publisher_.publish(int_msg)
                self.get_logger().info(f'Key "{lookup_key}", Sending command: {command_int}')
                # self.last_sent_command = command_int
            elif key == '\x03': # Check for CTRL-C
                self.get_logger().info('CTRL-C pressed, shutting down.')
                self.restore_terminal()
                raise KeyboardInterrupt
            # else: # Ignore other keys silently
            #     pass

    def restore_terminal(self):
         """Restores terminal settings."""
         if hasattr(self, 'settings'):
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

def main(args=None):
    """Main function."""
    rclpy.init(args=args)
    node = None
    settings = termios.tcgetattr(sys.stdin)
    try:
        node = WasdCommandPublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
             node.get_logger().info('KeyboardInterrupt received, shutting down node.')
    except Exception as e:
        if node:
            node.get_logger().error(f"An unexpected error occurred: {e}")
        else:
            print(f"An error occurred before node initialization: {e}")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        print("Terminal settings restored.")
        if node and rclpy.ok():
             node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        print("ROS 2 shutdown complete.")

if __name__ == '__main__':
    main()