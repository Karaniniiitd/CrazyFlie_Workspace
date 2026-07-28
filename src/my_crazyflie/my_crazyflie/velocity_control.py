import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time


from crazyflie_interfaces.srv import Arm

class VelocityController(Node):

    def __init__(self):
        super().__init__("velocity_controller")

        # Arm client
        self.arm_client = self.create_client(Arm, "/cf231/arm")
        while not self.arm_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for arm service...")

        # Publisher for velocity commands
        self.publisher = self.create_publisher(
            Twist,
            "/cf231/cmd_vel_legacy",
            10
        )

        self.get_logger().info("Velocity controller ready.")

    def arm(self):
        request = Arm.Request()
        request.arm = True
        self.get_logger().info("Arming drone...")
        future = self.arm_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Drone ARMED!")
        time.sleep(1)

    def send_velocity(self, roll=0.0, pitch=0.0, yaw_rate=0.0, thrust=0):
        """
        Send velocity command.

        roll      : tilt left/right  (degrees, range ~-30 to 30)
        pitch     : tilt fwd/back    (degrees, range ~-30 to 30)
        yaw_rate  : rotation speed   (degrees/sec)
        thrust    : motor thrust     (0 to 65535)
        """
        msg = Twist()
        msg.linear.x = pitch       # forward/backward
        msg.linear.y = roll        # left/right
        msg.linear.z = float(thrust)
        msg.angular.z = yaw_rate   # rotation

        self.publisher.publish(msg)

    def hover_in_place(self, duration_sec=3, thrust=38000):
        """Hold approximate hover thrust for a duration."""

        self.get_logger().info(f"Hovering for {duration_sec} seconds at thrust={thrust}...")

        end_time = time.time() + duration_sec
        rate = self.create_rate(20)  # 20 Hz

        while time.time() < end_time:
            self.send_velocity(thrust=thrust)
            rclpy.spin_once(self, timeout_sec=0.05)

        # Stop motors
        self.send_velocity(thrust=0)
        self.get_logger().info("Hover complete. Thrust set to 0.")


def main(args=None):

    rclpy.init(args=args)
    node = VelocityController()

    # 1. Arm the drone
    node.arm()

    # 2. Test: hover for 10 seconds using direct thrust
    # Thrust is at 43000, which should be enough for a visible lift-off.
    node.hover_in_place(duration_sec=10, thrust=43000)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
