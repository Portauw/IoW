import time
from config import cfg
from src.database import DbManager
from threading import Thread, Event
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import json
import sys
import os
from typing import Dict
from src.log import logger
from queue import Queue


class CountData:
    entered: bool = True
    timestamp: int = 0


class StateData:
    temperature: float = 15.0


class PlatformProcess(Thread):
    def __init__(self, stop_event: Event, data_q: Queue, cmd_q: Queue, count_interval: float = 2, state_interval: float = 120):
        self._stop_event = stop_event
        # self._count_interval = count_interval
        # self._state_interval = state_interval  # not actually used yet
        self._data_q: Queue = data_q
        self._cmd_q: Queue = cmd_q
        self._db_manager = DbManager()
        self._connected = False
        self._mqtt_connection = None
        self._mqtt_connected = False
        super().__init__()

    def on_counting_message_received(self, topic, payload, **kwargs):
        config_dict = json.loads(payload)
        logger.info(f"[MQTT] counting received @ {topic} : {payload}")

        n_max = config_dict['maxAllowed']
        n_estimated = config_dict['actualCount']

        self._data_q.put({'n_max': n_max, 'n_estimated': n_estimated})

    def on_cmd_message_received(self, topic, payload, **kwargs):
        config_dict = json.loads(payload)
        logger.info(f"[MQTT] command received @ {topic} : {payload}")

        cmd = config_dict['type']
        if cmd == "UPLOAD":
            self._cmd_q.put(cmd)

    def send_state(self, data: StateData):
        payload = json.dumps(data.__dict__)
        logger.info(f"[MQTT] state to topic '{cfg.mqtt_state_topic}': {payload}")
        self._mqtt_connection.publish(
            topic=cfg.mqtt_state_topic,
            payload=payload,
            qos=mqtt.QoS.AT_LEAST_ONCE)

    @staticmethod
    def get_temperature() -> float:
        platform = os.uname()
        if platform[1] == "raspberrypi":
            try:
                tmp: str = os.popen("/opt/vc/bin/vcgencmd measure_temp").readline()
                tmp = tmp.split("=")[-1]
                return float(tmp.split("'")[0])
            except Exception as e:
                logger.error(f"[MQTT][get_temperature] {e}")
        else:
            return 15.0

    def run(self) -> None:
        """
        TODO: Check if we can have longer keepalive on MQTT
        :return:
        """
        # Spin up mqtt resources
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

        counter = 0

        while not self._stop_event.is_set():

            if not self._mqtt_connected:

                while not cfg.has_device_id:
                    logger.info(f"[MQTT] No device_id set yet, sleeping for {cfg.eventSyncInterval} sec")
                    time.sleep(cfg.eventSyncInterval)

                try:
                    self._mqtt_connection = mqtt_connection_builder.mtls_from_path(
                        endpoint=cfg.mqtt_endpoint,
                        cert_filepath=cfg.mqtt_crt_absolute_path,
                        pri_key_filepath=cfg.mqtt_key_absolute_path,
                        client_bootstrap=client_bootstrap,
                        ca_filepath=cfg.mqtt_root_pem_absolute_path,
                        on_connection_interrupted=on_connection_interrupted,
                        on_connection_resumed=on_connection_resumed,
                        client_id=cfg.deviceId,
                        clean_session=False,
                        keep_alive_secs=15)

                    connect_future = self._mqtt_connection.connect()

                    # Future.result() waits until a result is available
                    connect_future.result()

                    self._mqtt_connected = True

                    logger.info(f"[MQTT] Connected")

                    logger.info(f"[MQTT] Subscribing to config messages")
                    subscribe_future, packet_id = self._mqtt_connection.subscribe(
                        topic=cfg.mqtt_config_topic,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                        callback=on_config_message_received)

                    subscribe_result = subscribe_future.result()
                    logger.info(f"[MQTT] subscribed to topic '{cfg.mqtt_state_topic}' : {str(subscribe_result['qos'])}")
                except Exception as e:
                    # Log the error, sleep for a while, and go to the next loop
                    logger.error(f"[MQTT] error on connection or subscibtion occured : {e}")
                    time.sleep(cfg.eventSyncInterval)
                    continue

                while not cfg.has_project_id:
                    logger.info(f"[MQTT] No project_id yet, sleeping for {cfg.eventSyncInterval} sec")
                    time.sleep(cfg.eventSyncInterval)

                #SUBSRIBE TO COUNTING MESSAGES
                try:
                    logger.info(f"[MQTT] Subscribing to counting messages")
                    subscribe_future, packet_id = self._mqtt_connection.subscribe(
                        topic=cfg.mqtt_count_topic,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                        callback=self.on_counting_message_received)

                    subscribe_result = subscribe_future.result()
                    logger.info(f"[MQTT] subscribed to topic '{cfg.mqtt_count_topic}' : {str(subscribe_result['qos'])}")
                except Exception as e:
                    logger.error(f"[MQTT] Error on subscription to counting : {e}")

                #SUBSRIBE TO COMMAND MESSAGES
                try:
                    logger.info(f"[MQTT] Subscribing to command topic")
                    subscribe_future, packet_id = self._mqtt_connection.subscribe(
                        topic=cfg.mqtt_cmd_topic,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                        callback=self.on_cmd_message_received)

                    subscribe_result = subscribe_future.result()
                    logger.info(f"[MQTT] subscribed to topic '{cfg.mqtt_cmd_topic}' : {str(subscribe_result['qos'])}")
                except Exception as e:
                    logger.error(f"[MQTT] Error on subscription to command topic : {e}")

            if self._mqtt_connected:

                unsynced_data = self._db_manager.get_unsynced()

                synced_ids = []

                for unsynced_record in unsynced_data:
                    data = CountData()
                    data.entered = unsynced_record.entered
                    data.timestamp = unsynced_record.timestamp

                    message = json.dumps(data.__dict__)
                    logger.info(f"[MQTT] Publishing count to topic '{cfg.mqtt_event_topic}' : {message}")
                    self._mqtt_connection.publish(
                        topic=cfg.mqtt_event_topic,
                        payload=message,
                        qos=mqtt.QoS.AT_LEAST_ONCE)

                    synced_ids.append(unsynced_record.id)

                self._db_manager.update_synced(synced_ids)

                # dirty af, but quicky testy
                counter += 1
                if counter >= int(cfg.stateSyncInterval / cfg.eventSyncInterval):
                    counter = 0
                    state_data = StateData()
                    state_data.temperature = self.get_temperature()
                    self.send_state(state_data)

            time.sleep(cfg.eventSyncInterval)
        logger.info(f"[MQTT] stopping thread")


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    logger.info(f"[MQTT] Connection interrupted. error: {error}")


def on_config_message_received(topic, payload, **kwargs):
    config_dict = json.loads(payload)
    logger.info(f"[MQTT] Config received @ {topic} : {payload}")

    cfg.update_config_with_dict(config_dict)

    if 'deviceConfig' in config_dict.keys():
        try:
            if config_dict['deviceConfig']['pipeline'][0]['name'] == 'TELLY' and \
                    config_dict['deviceConfig']['pipeline'][0]['type'] == 'CONFIG':
                logger.info(f"[MQTT] Saving new config")
                cfg.update_config_with_dict(config_dict['deviceConfig']['pipeline'][0]['properties'])
        except TypeError as e:
            logger.error(f"[MQTT] New config : Received TypeError {e} -- This might be normal when no platform configuration has been set yet")
        except Exception as e:
            logger.error(f"[MQTT] New config : Received unknown exception {e}")


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(f"[MQTT] Connection resumed. return code: {return_code}, session_present: {session_present}")

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        logger.info(f"[MQTT] Session did not persist, Resubscribing to topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    logger.info(f"[MQTT] Resubscribe results: {resubscribe_results}")

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, **kwargs):
    logger.info(f"[MQTT] Received message on unknown topic {topic} : {payload}")
