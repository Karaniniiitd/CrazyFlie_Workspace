import rclpy
from rclpy.node import Node

from crazyflie_interfaces.srv import Takeoff, Arm


class TakeoffClient(Node):

    def __init__(self):
        super().__init__("takeoff_client")

        # Arm client
        self.arm_client = self.create_client(Arm, "/cf231/arm")
        while not self.arm_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for arm service...")

        # Takeoff client
        self.takeoff_client = self.create_client(Takeoff, "/cf231/takeoff")
        while not self.takeoff_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for takeoff service...")

    def send_request(self, height=0.3, duration_sec=2):

        # 1. Arm
        arm_req = Arm.Request()
        arm_req.arm = True
        self.get_logger().info("Arming drone...")
        future_arm = self.arm_client.call_async(arm_req)
        rclpy.spin_until_future_complete(self, future_arm)
        self.get_logger().info("Drone ARMED!")

        # 2. Takeoff
        request = Takeoff.Request()
        request.group_mask = 0
        request.height = height
        request.duration.sec = duration_sec
        request.duration.nanosec = 0

        self.get_logger().info(f"Sending takeoff request to {height}m...")
        future = self.takeoff_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Takeoff completed! Hovering at target height.")


def main(args=None):

    rclpy.init(args=args)

    node = TakeoffClient()

    node.send_request()

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()