import rclpy
from rclpy.node import Node
from crazyflie_interfaces.srv import GoTo
from geometry_msgs.msg import Point


class GoToClient(Node):

    def __init__(self):
        super().__init__("goto_client")

        self.client = self.create_client(GoTo, "/cf231/go_to")

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for go_to service...")

    def go_to(self, x=0.0, y=0.0, z=0.3, yaw=0.0, duration_sec=2, relative=True):

        request = GoTo.Request()
        request.group_mask = 0
        request.relative = relative

        request.goal.x = x
        request.goal.y = y
        request.goal.z = z
        request.yaw = yaw

        request.duration.sec = duration_sec
        request.duration.nanosec = 0

        self.get_logger().info(
            f"Moving to x={x}, y={y}, z={z} (relative={relative})..."
        )

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        self.get_logger().info("GoTo command sent.")


def main(args=None):

    rclpy.init(args=args)
    node = GoToClient()

    # Example: move 0.2m forward (relative), then 0.2m back
    node.go_to(x=0.2, y=0.0, z=0.0, duration_sec=2, relative=True)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
