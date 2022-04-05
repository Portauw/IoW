import smbus2
import bme280
import time

# connect env sensor to I2c
env_sensor_config = {
    'name': "Environment Sensor",
    'port': 1,
    'address': 0x76,
    'type': "INPUT",
    'unit': ("°C", "hPa", " % rH"),
}


def init_sensor(config):
    _bus = smbus2.SMBus(config['port'])
    _address = config['address']
    try:
        bme280.load_calibration_params(_bus, _address)
        return _bus, _address
    except:  # noqa: E722
        print("Enviroment sensor setup failed")


def read_sensor():
    return bme280.sample(bus, address)


def measure_environment():
    raw_val = read_sensor()
    print("Temperature: {}".format(raw_val.temperature))
    print("Pressure: {}".format(raw_val.pressure))
    print("Humidity: {}".format(raw_val.humidity))

    measurement = {
        "Temperature": raw_val.temperature,
        "Pressure": raw_val.pressure,
        "Humidity": raw_val.humidity
    }

    return measurement


if __name__ == '__main__':
    bus, address = init_sensor(env_sensor_config)
    while True:
        measurement = measure_environment()
        for item in measurement:
            print(item)
        time.sleep(1)
