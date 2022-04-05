from multiprocessing import Process, Event, Queue, Lock

from src.base import EdgiseBase
from grove.modules.bme280 import bme280
import time
from config import cfg
import json


class EnvironmentSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, config_dict,
                 resource_lock: Lock, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._config_dict = config_dict
        self.bme_sensor = bme280()
        self.i2c_lock = resource_lock

        # Set oversampling
        # bme280 class defines OVRS_x0, .._x1, .._x2, .._x4, .._x8, .._x16
        # set_oversampling(osrs_h(humidity), osrs_t(temperature), osrs_p(pressure))
        # Set_oversampling > OVRS_x0 to enable the measurement, OVRS_x0 disables the measurement
        self.bme_sensor.set_oversampling(bme280.OVRS_x16, bme280.OVRS_x16, bme280.OVRS_x16)

        # Set internal IIR filter coefficient. 0 = no filter
        self.iir_filter = bme280.filter_16
        self.bme_sensor.set_filter(self.iir_filter)

        # Know values for pressure correction
        self.current_level_from_sea = 103  # Know height from sealevel m
        self.current_sea_level_pressure = 1027.5  # Forecast data: current pressure at sealevel
        self.count = 0  # Just for counting delays
        self.calibration_set = 0  # Help bit

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._config_dict['name'], logging_q=logging_q)

    def calibration_sequence(self):
        response_time = (2 ** self.iir_filter) * 2
        while self.count < response_time:
            self.info("Wait for sensor to settle before setting compensation! {} s".format(response_time - self.count))
            self.count += 1
            # set mode to FORCE that is one time measurement
            # bme280.MODE_SLEEP, ...FORCE, ...NORMAL
            # If normal mode also set t_sb that is standby time between measurements
            # if not specified is set to 1000ms bme280.t_sb_1000
            # Returns 1 on success 0 otherwise
            if not self.bme_sensor.set_mode(bme280.MODE_FORCE):
                self.info("\nMode change failed!")

            # Measure raw signals measurements are put in bme280.raw_* variables
            # Returns 1 on success otherwise 0
            if not self.bme_sensor.read_raw_signals():
                self.info("\nError in measurement!")

            # Compensate the raw signals
            if not self.bme_sensor.read_compensated_signals():
                self.info("\nError compensating values")

            time.sleep(1)

        # count == response time
        self.bme_sensor.set_pressure_calibration(level=self.current_level_from_sea,
                                                 pressure=self.current_sea_level_pressure)
        self.count = response_time + 1
        self.calibration_set = 1
        # Update the compensated values because new calibration value is given
        if not self.bme_sensor.read_compensated_signals():
            self.info("\nError compensating values")
        self.info("Sensor compensation is set")
        self.info("response time reached, finished calibration sequence!")
        # self.bme_sensor.write_reset()
        return

    def run(self) -> None:
        self.info("Starting Environment sensor")

        self.calibration_sequence()
        while not self._stop_event.is_set():
            if self.calibration_set:
                # measurement = {'deviceId': cfg.deviceId,
                #                'projectId': cfg.projectId,
                #                'timeStamp': time.time()
                #                }

                with self.i2c_lock:
                    self.bme_sensor.read_raw_signals()
                    # time.sleep(1)
                    self.bme_sensor.read_compensated_signals()
                    #   Only works if pressure calibration is done with set_pressure_calibration()
                    altitude = self.bme_sensor.get_altitude(self.current_sea_level_pressure)
                    # self.bme_sensor.write_reset()

                # self.info out the data
                self.info("Temperature: {} deg".format(self.bme_sensor.temperature))
                self.info("Pressure: {} hPa, where correction is {} hPa, sensor reading is {} hPa".format(
                    self.bme_sensor.calibrated_pressure, self.bme_sensor.calibration_pressure,
                    self.bme_sensor.pressure))
                self.info("Humidity: {} %RH".format(self.bme_sensor.humidity))
                self.info(
                    "altitude from sea level: {}m, {}".format(
                        altitude, self.bme_sensor.calibrated_pressure + altitude / 8))

                data = {"environmentSensorData": {
                    "temperature": self.bme_sensor.temperature,
                    "pressureSensorReading": self.bme_sensor.pressure,
                    "pressureCorrrection": self.bme_sensor.calibration_pressure,
                    "pressure": self.bme_sensor.calibrated_pressure,
                    "humidity": self.bme_sensor.humidity,
                    "altitude": altitude
                    }
                }
                measurement = {'data': data}
                self._output_q.put_nowait({'event': json.dumps(measurement)})
                time.sleep(10)
