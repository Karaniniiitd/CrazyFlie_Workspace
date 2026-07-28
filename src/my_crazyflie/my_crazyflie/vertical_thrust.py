import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from crazyflie_interfaces.srv import Arm
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterValue, ParameterType


class VerticalThrust(Node):

    def __init__(self):
        super().__init__("vertical_thrust")

        # ── Arm service ──────────────────────────────────────────
        self.arm_client = self.create_client(Arm, "/cf231/arm")
        while not self.arm_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for arm service...")

        # ── Firmware-param service (to reset Kalman filter) ──────
        self.param_client = self.create_client(
            SetParameters,
            "/crazyflie_server/set_parameters"
        )
        while not self.param_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for parameter service...")

        # ── cmd_vel_legacy publisher ──────────────────────────────
        self.publisher = self.create_publisher(
            Twist,
            "/cf231/cmd_vel_legacy",
            10
        )

        self.get_logger().info("Vertical thrust node ready.")

    # ──────────────────────────────────────────────────────────────
    # Step 0: Reset Kalman filter so drone is not in recovery state
    # ──────────────────────────────────────────────────────────────
    def reset_kalman(self):
        """
        Tell the Crazyflie: 'You are on the ground at (0,0,0), start fresh.'
        Without this, a 0-deck drone stays in recovery state and ignores thrust.
        """
        self.get_logger().info("Resetting Kalman filter...")

        param = Parameter()
        param.name = "cf231.params.kalman.resetEstimation"
        param.value = ParameterValue(
            type=ParameterType.PARAMETER_INTEGER,
            integer_value=1
        )

        req = SetParameters.Request()
        req.parameters = [param]

        future = self.param_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        # Give the filter 2 seconds to converge on the ground
        time.sleep(2.0)
        self.get_logger().info("Kalman filter reset complete.")

    # ──────────────────────────────────────────────────────────────
    # Step 1: Arm
    # ──────────────────────────────────────────────────────────────
    def arm(self):
        request = Arm.Request()
        request.arm = True
        self.get_logger().info("Arming drone...")
        future = self.arm_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Drone ARMED!")
        time.sleep(1)

    # ──────────────────────────────────────────────────────────────
    # Step 2: Send raw thrust
    # ──────────────────────────────────────────────────────────────
    def publish_thrust(self, thrust):
        msg = Twist()
        msg.linear.x = 0.0           # no forward/backward
        msg.linear.y = 0.0           # no left/right
        msg.linear.z = float(thrust)  # thrust: 0 to 65535
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = 0.0
        self.publisher.publish(msg)

    # ──────────────────────────────────────────────────────────────
    # Step 3: Apply thrust for a fixed duration
    # ──────────────────────────────────────────────────────────────
    def vertical_takeoff(self, thrust=42000, duration=5):
        self.get_logger().info(
            f"Applying thrust={thrust} for {duration}s ..."
        )
        start = time.time()
        while time.time() - start < duration:
            self.publish_thrust(thrust)
            rclpy.spin_once(self, timeout_sec=0.01)
            time.sleep(0.02)   # ~50 Hz publish rate

        self.get_logger().info("Stopping motors.")
        self.publish_thrust(0)
        time.sleep(1)


# ──────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = VerticalThrust()

    # 0. Reset Kalman — MUST run before anything else on a 0-deck drone
    node.reset_kalman()

    # 1. Arm
    node.arm()

    # 2. Apply thrust for 5 seconds
    # 42000 ≈ hover for a fully charged battery
    # Increase to 46000–50000 if it doesn't lift
    node.vertical_takeoff(thrust=42000, duration=5)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()