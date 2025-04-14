import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

# Mapping from received integer status to text
status_map = {
    0: "STOPPED",
    1: "MOVING FORWARD (W)",
    2: "MOVING LEFT (A)",
    3: "MOVING BACKWARD (S)",
    4: "MOVING RIGHT (D)",
}
# Default text if unknown integer received
unknown_status = "UNKNOWN STATUS RECEIVED"

class StatusDisplayNode(Node):
    """Node to subscribe to ESP32 status and print text."""
    def __init__(self):
        super().__init__('wasd_status_display_node')
        # Subscribe to the integer status topic from the ESP32
        self.subscription = self.create_subscription(
            Int32,
            'wasd_status', # Topic name published by ESP32
            self.status_callback,
            10) # QoS profile depth
        self.subscription  # prevent unused variable warning
        self.get_logger().info(f"'{self.get_name()}' started.")
        self.get_logger().info("Listening for status on topic: /wasd_status")
        self.last_printed_status = None # Keep track to avoid repetitive printing

    def status_callback(self, msg):
        """Processes incoming status messages."""
        received_status_int = msg.data
        # Look up the text status, use default if not found
        status_text = status_map.get(received_status_int, unknown_status)

        # Only print if the status has changed
        if status_text != self.last_printed_status:
            self.get_logger().info(f'Current Status: {status_text}')
            self.last_printed_status = status_text

def main(args=None):
    """Main function."""
    rclpy.init(args=args)
    node = StatusDisplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('KeyboardInterrupt received, shutting down node.')
    finally:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        node.destroy_node()
        if rclpy.ok():
             rclpy.shutdown()

if __name__ == '__main__':
    main()