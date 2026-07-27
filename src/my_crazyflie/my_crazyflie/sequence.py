import rclpy
from rclpy.node import Node
from crazyflie_interfaces.srv import Takeoff, Land
from crazyflie_interfaces.srv import Takeoff, Land, Arm
import time


class SequenceClient(Node):

    def __init__(self):
        super().__init__("sequence_client")

        # Arm client
        self.arm_client = self.create_client(Arm, "/cf231/arm")
        while not self.arm_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for arm service...")

        # Takeoff client
        self.takeoff_client = self.create_client(Takeoff, "/cf231/takeoff")
        while not self.takeoff_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for takeoff service...")

        # Land client
        self.land_client = self.create_client(Land, "/cf231/land")
        while not self.land_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for land service...")

    def takeoff(self, height=0.3, duration_sec=2):

        request = Takeoff.Request()
        request.group_mask = 0
        request.height = height
        request.duration.sec = duration_sec
        request.duration.nanosec = 0

        self.get_logger().info(f"Taking off to {height}m ...")
        future = self.takeoff_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Takeoff command sent.")

    def land(self, duration_sec=2):

        request = Land.Request()
        request.group_mask = 0
        request.height = 0.0
        request.duration.sec = duration_sec
        request.duration.nanosec = 0

        self.get_logger().info("Landing ...")
        future = self.land_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Land command sent.")

    def arm(self):
        request = Arm.Request()
        request.arm = True
        self.get_logger().info("Arming drone...")
        future = self.arm_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Drone ARMED!")
        time.sleep(1)

    def run_sequence(self):

        # Step 0: Arm
        self.arm()

        # Step 1: Takeoff
        self.takeoff(height=0.3, duration_sec=2)

        # Step 2: Hover for 3 seconds
        self.get_logger().info("Hovering for 3 seconds...")
        time.sleep(5)   # wait for takeoff (2s) + hover (3s)

        # Step 3: Land
        self.land(duration_sec=2)

        # Step 4: Wait for landing to complete
        self.get_logger().info("Waiting for landing to complete...")
        time.sleep(3)

        self.get_logger().info("Sequence complete!")


def main(args=None):

    rclpy.init(args=args)
    node = SequenceClient()
    node.run_sequence()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
