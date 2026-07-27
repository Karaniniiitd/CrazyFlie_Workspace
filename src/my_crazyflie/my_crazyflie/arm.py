import rclpy
from rclpy.node import Node
from crazyflie_interfaces.srv import Arm


class ArmClient(Node):

    def __init__(self):
        super().__init__("arm_client")

        self.client = self.create_client(Arm, "/cf231/arm")

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for arm service...")

    def arm(self):
        request = Arm.Request()
        request.arm = True          # True = arm, False = disarm
        self.get_logger().info("Arming drone...")
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Drone ARMED. Ready to fly!")


def main(args=None):
    rclpy.init(args=args)
    node = ArmClient()
    node.arm()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
