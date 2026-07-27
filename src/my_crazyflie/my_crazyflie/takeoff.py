import rclpy
from rclpy.node import Node

from crazyflie_interfaces.srv import Takeoff


class TakeoffClient(Node):

    def __init__(self):
        super().__init__("takeoff_client")

        self.client = self.create_client(
            Takeoff,
            "/cf231/takeoff"
        )

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for takeoff service...")

    def send_request(self):

        request = Takeoff.Request()

        request.group_mask = 0
        request.height = 0.2
        request.duration.sec = 2
        request.duration.nanosec = 0

        self.get_logger().info("Sending takeoff request...")

        future = self.client.call_async(request)

        rclpy.spin_until_future_complete(self, future)

        self.get_logger().info("Takeoff request completed.")


def main(args=None):

    rclpy.init(args=args)

    node = TakeoffClient()

    node.send_request()

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()