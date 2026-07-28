"""
anti_drift_controller.py
────────────────────────
Closed-loop P-controller for Crazyflie 2.1 (0-deck configuration).

How it works
────────────
1. Reset the onboard Kalman filter → drone knows it starts at (0,0,0).
2. Arm the drone.
3. Gradually ramp up thrust until we leave the ground.
4. Subscribe to /cf231/pose (Kalman-estimated position from IMU dead-reckoning).
5. Every control tick compute:

      err_x  = target_x  - current_x     (forward error)
      err_y  = target_y  - current_y     (side error)
      err_z  = target_z  - current_z     (height error)

      thrust = HOVER_THRUST  +  Kp_z  * err_z
      pitch  = Kp_xy * err_x            (pitch forward/back to kill x drift)
      roll   = Kp_xy * err_y            (roll left/right to kill y drift)

6. Publish Twist on /cf231/cmd_vel_legacy at 50 Hz.

WARNING
───────
Without a Flow Deck the IMU dead-reckoning drifts after ~10–15 s.
This controller will reduce drift significantly but not eliminate it.
Buy a Flow Deck v2 for long-term hover stability.

Usage
─────
  ros2 run my_crazyflie anti_drift_controller
"""

import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseStamped
from crazyflie_interfaces.srv import Arm, Land
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterValue, ParameterType


# ──────────────────────────────────────────────────────────────────
#  TUNABLE CONSTANTS — adjust these for your drone
# ──────────────────────────────────────────────────────────────────
HOVER_THRUST   = 42000   # thrust (0–65535) that keeps drone roughly level
                         # increase if it can't lift, decrease if it rockets up

TARGET_X       = 0.0     # desired x position (m)
TARGET_Y       = 0.0     # desired y position (m)
TARGET_Z       = 0.4     # desired altitude   (m)

Kp_z           = 8000    # proportional gain for altitude  (thrust units / m)
Kp_xy          = 5.0     # proportional gain for x/y drift (degrees / m)

MAX_TILT       = 10.0    # maximum allowed roll/pitch angle (degrees)
MAX_THRUST     = 55000   # safety ceiling on thrust
MIN_THRUST     = 20000   # below this the drone will fall

FLIGHT_TIME    = 10.0    # total flight duration (seconds)
CONTROL_HZ     = 50      # control loop frequency
# ──────────────────────────────────────────────────────────────────


class AntiDriftController(Node):

    def __init__(self):
        super().__init__("anti_drift_controller")

        # ── Current estimated position (updated by pose callback) ──
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.pos_z = 0.0
        self.pose_received = False

        # ── Services ───────────────────────────────────────────────
        self.arm_client = self.create_client(Arm, "/cf231/arm")
        while not self.arm_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for arm service...")

        self.land_client = self.create_client(Land, "/cf231/land")
        while not self.land_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for land service...")

        self.param_client = self.create_client(
            SetParameters, "/crazyflie_server/set_parameters"
        )
        while not self.param_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for parameter service...")

        # ── Publisher ──────────────────────────────────────────────
        self.cmd_pub = self.create_publisher(
            Twist, "/cf231/cmd_vel_legacy", 10
        )

        # ── Subscriber (pose feedback from Kalman filter) ──────────
        self.pose_sub = self.create_subscription(
            PoseStamped,
            "/cf231/pose",
            self._pose_callback,
            10
        )

        self.get_logger().info("Anti-drift controller initialised.")

    # ────────────────────────────────────────────────────────────────
    def _pose_callback(self, msg: PoseStamped):
        """Store the latest Kalman-estimated position."""
        self.pos_x = msg.pose.position.x
        self.pos_y = msg.pose.position.y
        self.pos_z = msg.pose.position.z
        self.pose_received = True

    # ────────────────────────────────────────────────────────────────
    def reset_kalman(self):
        """
        Reset the onboard Kalman filter.
        This exits the 'recovery state' that prevents a 0-deck drone from flying.
        """
        self.get_logger().info("Resetting Kalman filter (clearing recovery state)...")
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
        time.sleep(2.0)
        self.get_logger().info("Kalman reset done. Drone thinks it is at (0, 0, 0).")

    # ────────────────────────────────────────────────────────────────
    def arm(self):
        req = Arm.Request()
        req.arm = True
        self.get_logger().info("Arming drone...")
        future = self.arm_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info("Drone ARMED!")
        time.sleep(1.0)

    # ────────────────────────────────────────────────────────────────
    def _clamp(self, value, low, high):
        return max(low, min(high, value))

    # ────────────────────────────────────────────────────────────────
    def _publish_cmd(self, roll, pitch, yaw_rate, thrust):
        """Publish one control command at 50 Hz."""
        msg = Twist()
        msg.linear.x  = float(pitch)     # forward/backward tilt
        msg.linear.y  = float(roll)      # left/right tilt
        msg.linear.z  = float(thrust)    # vertical thrust
        msg.angular.z = float(yaw_rate)  # yaw (kept at 0)
        self.cmd_pub.publish(msg)

    # ────────────────────────────────────────────────────────────────
    def run_controller(self):
        """
        Main closed-loop control loop.

        Phase 1 – Ramp up:  gradually increase thrust so the drone
                             lifts off gently.
        Phase 2 – Hold:     P-controller keeps drone near target.
        Phase 3 – Land:     cut thrust gradually.
        """
        dt        = 1.0 / CONTROL_HZ
        end_time  = time.time() + FLIGHT_TIME

        # ── Phase 1: gentle ramp-up (~1 second) ──────────────────
        self.get_logger().info("Phase 1: ramping up thrust...")
        for thrust in range(0, HOVER_THRUST, 2000):
            self._publish_cmd(0, 0, 0, thrust)
            time.sleep(0.05)

        # ── Phase 2: closed-loop P control ───────────────────────
        self.get_logger().info(
            f"Phase 2: P-control → target ({TARGET_X}, {TARGET_Y}, {TARGET_Z} m)"
        )

        while time.time() < end_time:
            # Spin once to process the pose subscription callback
            rclpy.spin_once(self, timeout_sec=dt)

            # ── Compute position errors ──────────────────────────
            err_x = TARGET_X - self.pos_x   # positive → drone is behind target
            err_y = TARGET_Y - self.pos_y   # positive → drone is right of target
            err_z = TARGET_Z - self.pos_z   # positive → drone is below target

            # ── P controller outputs ─────────────────────────────
            thrust = HOVER_THRUST + Kp_z  * err_z
            pitch  =               Kp_xy * err_x   # tilt fwd to move in +x
            roll   =             - Kp_xy * err_y   # tilt right to move in +y

            # ── Safety clamps ────────────────────────────────────
            thrust = self._clamp(thrust, MIN_THRUST, MAX_THRUST)
            pitch  = self._clamp(pitch, -MAX_TILT, MAX_TILT)
            roll   = self._clamp(roll,  -MAX_TILT, MAX_TILT)

            self._publish_cmd(roll, pitch, 0.0, thrust)

            # ── Debug readout ────────────────────────────────────
            self.get_logger().info(
                f"pos=({self.pos_x:.2f},{self.pos_y:.2f},{self.pos_z:.2f}) "
                f"err=({err_x:.2f},{err_y:.2f},{err_z:.2f}) "
                f"thr={int(thrust)} pitch={pitch:.1f}° roll={roll:.1f}°"
            )

        # ── Phase 3: ramp down ────────────────────────────────────
        self.get_logger().info("Phase 3: ramping down thrust (landing)...")
        for thrust in range(HOVER_THRUST, 0, -2000):
            self._publish_cmd(0, 0, 0, thrust)
            time.sleep(0.05)

        self._publish_cmd(0, 0, 0, 0)
        self.get_logger().info("Sequence complete.")


# ──────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = AntiDriftController()

    node.reset_kalman()   # Step 0 – exit recovery state
    node.arm()            # Step 1 – arm motors
    node.run_controller() # Step 2 – fly with P control

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
