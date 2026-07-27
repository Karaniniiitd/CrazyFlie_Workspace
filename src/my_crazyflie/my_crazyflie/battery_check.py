"""
battery_check.py
----------------
Connects directly to the Crazyflie via cflib (no ROS server needed)
and reads the battery voltage.

Usage:
    python3 battery_check.py
"""

import logging
import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.log import LogConfig

# ── Config ────────────────────────────────────────────────────────────────────
URI = 'radio://0/80/2M/E7E7E7E7E7'   # change if needed
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.ERROR)


def battery_callback(timestamp, data, logconf):
    voltage = data['pm.vbat']
    charge  = data.get('pm.batteryLevel', -1)

    # 3.7V nominal LiPo 1S: 4.20V full → 3.00V cutoff
    if voltage >= 4.10:
        level = "🟢 Full     (~100%)"
    elif voltage >= 3.90:
        level = "🟡 Good     (~75%)"
    elif voltage >= 3.75:
        level = "🟠 Medium   (~50%)"
    elif voltage >= 3.50:
        level = "🔴 Low      (~25%) — charge soon"
    elif voltage >= 3.20:
        level = "⛔ Very Low (~10%) — land & charge NOW"
    else:
        level = "💀 Critical  — may damage battery!"

    print(f"\n  Battery Voltage : {voltage:.3f} V")
    if charge >= 0:
        print(f"  Battery Level   : {charge}%")
    print(f"  Status          : {level}\n")


def check_battery(uri):
    cflib.crtp.init_drivers()
    print(f"Connecting to Crazyflie at {uri} ...")

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        print("Connected!")

        log_conf = LogConfig(name='Battery', period_in_ms=500)
        log_conf.add_variable('pm.vbat', 'float')

        try:
            log_conf.add_variable('pm.batteryLevel', 'uint8_t')
        except Exception:
            pass  # older firmware may not have this variable

        scf.cf.log.add_config(log_conf)
        log_conf.data_received_cb.add_callback(battery_callback)
        log_conf.start()

        time.sleep(2)   # read for 2 seconds

        log_conf.stop()
        print("Done.")


if __name__ == '__main__':
    check_battery(URI)
