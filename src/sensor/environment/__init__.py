from multiprocessing import Process, Event, Queue

from src.base import EdgiseBase
from time import sleep
from grove.modules.bme280 import bme280


class EnvironmentSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, input_q: Queue, output_q: Queue, config_dict, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._input_q: Queue = input_q
        self._output_q: Queue = output_q
        self._config_dict = config_dict
        self.bme_sensor = bme280()

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
            print("Wait for sensor to settle before setting compensation!", response_time - self.count, "s")
            self.count += 1
            # set mode to FORCE that is one time measurement
            # bme280.MODE_SLEEP, ...FORCE, ...NORMAL
            # If normal mode also set t_sb that is standby time between measurements
            # if not specified is set to 1000ms bme280.t_sb_1000
            # Returns 1 on success 0 otherwise
            if not self.bme_sensor.set_mode(bme280.MODE_FORCE):
                print("\nMode change failed!")

            # Measure raw signals measurements are put in bme280.raw_* variables
            # Returns 1 on success otherwise 0
            if not self.bme_sensor.read_raw_signals():
                print("\nError in measurement!")

            # Compensate the raw signals
            if not self.bme_sensor.read_compensated_signals():
                print("\nError compensating values")

            sleep(1)

        # count == response time
        self.bme_sensor.set_pressure_calibration(level=self.current_level_from_sea,
                                                 pressure=self.current_sea_level_pressure)
        self.count = response_time + 1
        self.calibration_set = 1
        # Update the compensated values because new calibration value is given
        if not self.bme_sensor.read_compensated_signals():
            print("\nError compensating values")
        print("Sensor compensation is set")
        self.info("response time reached, finished calibration sequence!")

    def run(self) -> None:
        self.info("Starting vibration sensor")

        self.calibration_sequence()
        while not self._stop_event.is_set():
            if not self._input_q.empty() and self.calibration_set:
                measurement_dict = self._input_q.get_nowait()

                raw_val = self.bme_sensor.read_raw_signals()
                comp_val = self.bme_sensor.read_compensated_signals()
                # Only works if pressure calibration is done with set_pressure_calibration()
                altitude = bme_sensor.get_altitude(current_sea_level_pressure)

                # Print out the data
                print("Temperature: %.2f" % bme_sensor.temperature, chr(176) + "C")
                print("Pressure: %.2fhPa, where correction is %.2fhPa, sensor reading is %.2fhPa"
                      % (bme_sensor.calibrated_pressure, bme_sensor.calibration_pressure, bme_sensor.pressure))
                print("Humidity: %.2f" % bme_sensor.humidity, "%RH")
                print(
                    "altitude from sea level: %.3fm, %.3f" % (altitude, bme_sensor.calibrated_pressure + altitude / 8))
                print("\n")

                measurement = {
                    "Temperature": self.bme_sensor.temperature,
                    "Pressure Sensor Reading": self.bme_sensor.pressure,
                    "Pressure Corrrection": self.bme_sensor.calibration_pressure,
                    "Pressure": self.bme_sensor.calibrated_pressure,
                    "Humidity": self.bme_sensor.humidity,
                    "Altitude": altitude
                }
                measurement_dict[self._config_dict['name']] = measurement
                self._output_q.put_nowait(measurement_dict)
                time.sleep(2)
