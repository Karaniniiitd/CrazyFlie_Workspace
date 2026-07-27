import rclpy
from rclpy.node import Node
from std_srvs.srv import Empty


class EmergencyClient(Node):

    def __init__(self):
        super().__init__("emergency_client")

        self.client = self.create_client(
            Empty,
            "/cf231/emergency"
        )

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for emergency service...")

    def send_request(self):

        request = Empty.Request()

        self.get_logger().warn("!!! SENDING EMERGENCY STOP !!!")

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        self.get_logger().warn("Emergency stop sent. Motors killed.")


def main(args=None):

    rclpy.init(args=args)
    node = EmergencyClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
