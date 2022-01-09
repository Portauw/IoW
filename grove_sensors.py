import time
from math import sqrt

from grove.adc import ADC

# AC Sensor
AC_sensor_config = {
    'name': "Electricity sensor",
    'pin': 0,
    'type': "INPUT",
    'unit': "mA",
}
# grovepi.pinMode(AC_sensor_config['pin'], AC_sensor_config['type'])
ac_adc = ADC()


def read_ac_sensor():
    sensor_value = ac_adc.read(AC_sensor_config['pin'])
    return sensor_value


def calc_amplitude_current(sensor_value):
    VCC = 5
    return float(sensor_value / 1024 * VCC / 800 * 2000000)


def calc_RMS_current(amplitude_current):
    return amplitude_current / sqrt(2)


def calc_avg_power_consumption(RMS_current):
    return 230 * RMS_current


def measure_AC():
    raw_val = read_ac_sensor()
    print("Raw Value: {}".format(raw_val))
    amplitude_current = calc_amplitude_current(raw_val)
    print("A I Value: {}".format(amplitude_current))
    rms_current = calc_RMS_current(amplitude_current)
    print("RMS I Value: {}".format(rms_current))
    avg_power = calc_avg_power_consumption(rms_current)
    print("AVG W Value: {}".format(avg_power))

    measurement = {
        'RawVal': raw_val,
        'CurrentAmp': amplitude_current,
        'RMSCurrent': rms_current,
        'AVGPower': avg_power
    }
    return measurement


# Vibration sensor

# connect vibration sensor to analog port A2
vibration_sensor_config = {
    'name': 'Vibration sensor',
    'pin': 2,
    'type': 'INPUT',
    'unit': 'MHz',
}
# grovepi.pinMode(vibration_sensor_config['pin'], vibration_sensor_config['type'])
vibr_adc = ADC()


def read_vbr_sensor():
    sensor_value = vibr_adc.read(vibration_sensor_config['pin'])
    return sensor_value


def measure_vibration():
    raw_val = read_vbr_sensor()
    print("Raw Value Vibration: {}".format(raw_val))

    measurement = {
        'RawVal': raw_val,
    }
    return measurement


if __name__ == '__main__':

    while True:
        measurement_ac = measure_AC()

        time.sleep(1)
        measurement_vibr = measure_vibration()

        time.sleep(1)
