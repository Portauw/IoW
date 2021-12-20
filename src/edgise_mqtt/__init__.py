import time
from config import cfg
# from src.database import DbManager
from threading import Thread, Event
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import json
import sys
import os
from typing import Dict, List, Callable
from queue import Empty
from awscrt.mqtt import Future
from src.base import EdgiseBase
from multiprocessing import Queue as mpQueue



# class CountData:
#     entered: bool = True
#     timestamp: int = 0


# class StateData:
#     temperature: float = 15.0


OUT_TOPIC_TRANSLATOR: Dict = {'state': cfg.mqtt_state_topic,
                              'event': cfg.mqtt_event_topic,
                              'log': cfg.mqtt_log_topic}


class EdgiseMQTT(Thread, EdgiseBase):
    def __init__(self, stop_event: Event, data_q: mpQueue, cmd_qs: List[mpQueue], send_q: mpQueue, logging_q: mpQueue):
        self._stop_event = stop_event
        self._data_q: mpQueue = data_q
        self._cmd_qs: List[mpQueue] = cmd_qs
        self._send_q: mpQueue = send_q
        # self._db_manager = DbManager()
        self._connected = False
        self._mqtt_connection = None
        self._mqtt_connected = False

        self.event_loop_group = io.EventLoopGroup(1)
        self.host_resolver = io.DefaultHostResolver(self.event_loop_group)
        self.client_bootstrap = io.ClientBootstrap(self.event_loop_group, self.host_resolver)

        self._incoming_msg = None

        Thread.__init__(self)
        EdgiseBase.__init__(self, name="MQTT", logging_q=logging_q)

    # Callback when the subscribed topic receives a message
    def on_message_received(self, topic, payload, **kwargs):
        self.info(f"Received message on unknown topic {topic} : {payload}")

    def on_counting_message_received(self, topic, payload, **kwargs):
        config_dict = json.loads(payload)
        self.info(f"Counting received @ {topic} : {payload}")

        n_max = config_dict['maxAllowed']
        n_estimated = config_dict['actualCount']

        self._data_q.put({'n_max': n_max, 'n_estimated': n_estimated})

    def on_cmd_message_received(self, topic, payload, **kwargs):
        config_dict = json.loads(payload)
        self.info(f"Command received @ {topic} : {payload}")

        try:
            cmd = config_dict['type']

            for q in self._cmd_qs:
                try:
                    q.put(cmd, block=True, timeout=0.01)
                except Exception as e:
                    self.error(f"Error putting command into Q : {e}")

        except Exception as e:
            self.error(f"Error retrieving command type : {e}")

    def _connect_mqtt(self) -> bool:
        if not self._mqtt_connected:
            try:
                self._mqtt_connection = mqtt_connection_builder.mtls_from_path(
                    endpoint=cfg.mqtt_endpoint,
                    cert_filepath=cfg.mqtt_crt_absolute_path,
                    pri_key_filepath=cfg.mqtt_key_absolute_path,
                    client_bootstrap=self.client_bootstrap,
                    ca_filepath=cfg.mqtt_root_pem_absolute_path,
                    on_connection_interrupted=self.on_connection_interrupted,
                    on_connection_resumed=self.on_connection_resumed,
                    client_id=cfg.deviceId,
                    clean_session=False,
                    keep_alive_secs=15)

                connect_future = self._mqtt_connection.connect()

                # Future.result() waits until a result is available
                connect_future.result()

                self._mqtt_connected = True
                self.info(f"Connected")
                return True

            except Exception as e:
                self._mqtt_connected = False
                self.error(f"Connection error : {e}")
                return False

    def _subscribe_on_topic(self, topic: str, callback: Callable = on_message_received):
        try:
            subscribe_future, packet_id = self._mqtt_connection.subscribe(
                topic=topic,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=callback)

            subscribe_result = subscribe_future.result()

            self.info(f"Subscribed to topic '{str(subscribe_result['topic'])}' : {str(subscribe_result['qos'])}")
        except Exception as e:
            self.error(f"Error while subscribing to {topic} : {e}")

    def _publish_on_topic(self, topic: str, message) -> bool:
        self.info(f"Publishing to topic '{topic}' : {message}")
        try:
            publish_future, publish_packet = self._mqtt_connection.publish(
                topic=topic,
                payload=message,
                qos=mqtt.QoS.AT_LEAST_ONCE)

            publish_result = publish_future.result()

            self.info(f"Publish succeeded : {publish_result}")

            return True
        except Exception as e:
            self.error(f"Error while publishing msg '{message}' to topic '{topic}' : {e}")
            return False

    # def _incoming_data_handler(self, incoming: Dict):
    #     try:
    #         for topic, message in incoming.items():
    #             if topic in OUT_TOPIC_TRANSLATOR.keys():
    #                 while not self._publish_on_topic(OUT_TOPIC_TRANSLATOR[topic], message):
    #                     self.info(f"Connection issues, trying to reconnect and send the message again")
    #                     self._connect_mqtt()
    #             else:
    #                 self.error(f"Something tried to send a message on an unknown topic '{topic}' : {message}")
    #
    #     except Exception as e:
    #         self.error(f"Error with incoming : {incoming} -- Error: {e} ")

    def _incoming_data_handler(self):
        try:
            result = {}
            for topic, message in self._incoming_msg.items():
                if topic in OUT_TOPIC_TRANSLATOR.keys():
                    if not self._publish_on_topic(OUT_TOPIC_TRANSLATOR[topic], message):
                        self.info(f"Connection issues, trying to reconnect")
                        self._connect_mqtt()
                        result[topic] = message
                else:
                    self.error(f"Something tried to send a message on an unknown topic '{topic}' : {message}")

            if len(result) == 0:
                self._incoming_msg = None
            else:
                self._incoming_msg = result

        except Exception as e:
            self.error(f"Error with incoming : {self._incoming_msg} -- Error: {e} ")

    def run(self) -> None:
        """
        :return:
        """

        while not self._stop_event.is_set():

            if not self._mqtt_connected:

                # Wait until registration is done
                while not cfg.has_device_id:
                    self.info(f"No device_id set yet, sleeping for {cfg.event_sync_interval * 10.} sec")
                    time.sleep(cfg.event_sync_interval * 10.)

                # Connect to the MQTT broker
                self._connect_mqtt()

                # Subscribe on config topic, which will allow us to get a project ID and a config for the device
                self._subscribe_on_topic(cfg.mqtt_config_topic, self.on_config_message_received)

                # Wait until device has been configured
                while not cfg.has_project_id:
                    self.info(f"No project_id yet, sleeping for {cfg.event_sync_interval * 10.} sec")
                    time.sleep(cfg.event_sync_interval * 10.)

                # Subscribe to count topic
                self._subscribe_on_topic(cfg.mqtt_count_topic, self.on_counting_message_received)

                # Subscribe to command topic
                self._subscribe_on_topic(cfg.mqtt_cmd_topic, self.on_cmd_message_received)

            else:

                try:
                    if self._incoming_msg is None:
                        self._incoming_msg = self._send_q.get_nowait()

                    self._incoming_data_handler()
                except Empty:
                    time.sleep(cfg.event_sync_interval)
                    pass

        self.info("Quitting.")

    # Callback when connection is accidentally lost.
    def on_connection_interrupted(self, connection, error, **kwargs):
        self.info(f"Connection interrupted. error: {error}")

    def on_config_message_received(self, topic, payload, **kwargs):
        config_dict = json.loads(payload)
        self.info(f"Config received @ {topic} : {payload}")

        cfg.update_config_with_dict(config_dict)  # this saves the device_id and project_id

        if 'deviceConfig' in config_dict.keys():
            try:
                if config_dict['deviceConfig']['pipeline'][0]['name'] == 'TELLY' and \
                        config_dict['deviceConfig']['pipeline'][0]['type'] == 'CONFIG':
                    self.info(f"Saving new config")
                    # this saves the rest of the config
                    cfg.update_config_with_dict(config_dict['deviceConfig']['pipeline'][0]['properties'])
            except TypeError as e:
                self.error(f"New config : Received TypeError {e} -- This might be normal when no platform configuration has been set yet")
            except Exception as e:
                self.error(f"New config : Received unknown exception {e}")

    # Callback when an interrupted connection is re-established.
    def on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        self.info(f"Connection resumed. return code: {return_code}, session_present: {session_present}")

        if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
            self.info(f"Session did not persist, Resubscribing to topics...")
            resubscribe_future, _ = connection.resubscribe_existing_topics()

            # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
            # evaluate result with a callback instead.
            resubscribe_future.add_done_callback(self.on_resubscribe_complete)

    def on_resubscribe_complete(self, resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        self.info(f"Resubscribe results: {resubscribe_results}")

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))



