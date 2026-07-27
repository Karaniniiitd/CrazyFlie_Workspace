import rclpy
from rclpy.node import Node
from crazyflie_interfaces.srv import Land


class LandClient(Node):

    def __init__(self):
        super().__init__("land_client")

        self.client = self.create_client(
            Land,
            "/cf231/land"
        )

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for land service...")

    def send_request(self):

        request = Land.Request()
        request.group_mask = 0
        request.height = 0.0
        request.duration.sec = 2
        request.duration.nanosec = 0

        self.get_logger().info("Sending land request...")

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        self.get_logger().info("Land request completed. Drone landing.")


def main(args=None):

    rclpy.init(args=args)
    node = LandClient()
    node.send_request()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
