import os
import json
import base_config
from typing import List, Dict


class Config:

    def __init__(self):
        self.root_dir: str = os.path.dirname(os.path.abspath(__file__))
        self.logEnabled: bool = False
        self.updateBranch: str = ''
        self.sqlitePath: str = ''
        self.modelPath: str = ''
        self.zones: List[Dict] = []
        self.deviceId: str = ''
        self.projectId: str = ''
        self.screenUpdateInterval: float = 0.3
        self.eventSyncInterval: float = 0.5
        self.stateSyncInterval: float = 600
        self.mqtt_endpoint: str = base_config.ENDPOINT
        self.mqtt_crt_path: str = base_config.CRT_PATH
        self.mqtt_key_path: str = base_config.KEY_PATH
        self.mqtt_root_pem_path: str = base_config.ROOT_PEM
        self.config_file_path: str = base_config.CONFIG_FILE
        self.logging_file_path: str = base_config.LOGGING_FILE
        self.dry_config_file_path: str = base_config.DRY_CONFIG_FILE
        self.upload_folder_path: str = base_config.UPLOAD_FOLDER_PATH
        self.registration_url: str = base_config.REGISTRATION_URL
        self.logging_levels: List = base_config.LOGGING_LEVELS
        self.logging_error: int = base_config.LOGGING_ERROR
        self.logging_info: int = base_config.LOGGING_INFO
        self.logging_debug: int = base_config.LOGGIN_DEBUG
        self.MQTTLoggingLevel: int = 1
        self.screenLoggingLevel: int = 3
        self.screenLoggingRejectionList: List[str] = []
        self.MQTTLoggingRejectionList: List[str] = ["MQTT"]
        self.MQTTLogRateLimiter: int = 5
        self.screenLogRateLimiter: int = 20

        self.topicPrefix: str = "/"
        self.platformApiUrl: str = "https://platform-test.edgise.com/api/"
        self.uploaderInterval: float = 2

        self.main_filename: str = "main.py"
        self.main_file_path: str = f"{self.root_dir}/{self.main_filename}"

        self.cronosLoginUrl: str = ''
        self.cronosIncreaseUrl: str = ''
        self.cronosDecreaseUrl: str = ''
        self.cronosGetStatsUrl: str = ''
        self.cronosGetLocationUrl: str = ''

        self.cronosUsername: str = ''
        self.cronosPassword: str = ''

        # fetch full dry config
        self.load_config_from_file(self.dry_config_file_absolute_path)

        # load from dedicated device config what is possible
        self.load_config_from_file(self.config_file_absolute_path)

    @property
    def upload_folder_absolute_path(self) -> str:
        return f"{self.root_dir}/{self.upload_folder_path}"

    @property
    def project_id(self) -> str:
        return self.projectId

    @property
    def device_id(self) -> str:
        return self.deviceId

    @property
    def uploader_interval(self) -> float:
        return self.uploaderInterval

    @property
    def mqtt_log_rate_limiter(self) -> int:
        return self.MQTTLogRateLimiter

    @property
    def screen_log_rate_limiter(self) -> int:
        return self.screenLogRateLimiter

    @property
    def mqtt_logging_level(self) -> int:
        return self.MQTTLoggingLevel

    @property
    def screen_logging_level(self) -> int:
        return self.screenLoggingLevel

    @property
    def mqtt_logging_rejection_list(self) -> List[str]:
        return self.MQTTLoggingRejectionList

    @property
    def screen_logging_rejection_list(self) -> List[str]:
        return self.screenLoggingRejectionList

    @property
    def platform_api_url(self):
        return self.platformApiUrl

    @property
    def file_upload_url(self) -> str:
        ret = None

        if self.has_project_id and self.has_device_id:
            ret = f"{self.platform_api_url}projects/{cfg.projectId}/devices/{cfg.deviceId}/files"

        return ret

    @property
    def has_device_id(self) -> bool:
        return True if self.deviceId != '' else False

    @property
    def update_branch(self) -> str:
        return self.updateBranch

    @property
    def has_project_id(self) -> bool:
        return True if self.projectId != '' else False

    @property
    def ai_model_absolute_path(self) -> str:
        return f"{self.root_dir}/{self.modelPath}"

    @property
    def mqtt_crt_absolute_path(self) -> str:
        return f"{self.root_dir}/{self.mqtt_crt_path}"

    @property
    def mqtt_key_absolute_path(self) -> str:
        return f"{self.root_dir}/{self.mqtt_key_path}"

    @property
    def mqtt_root_pem_absolute_path(self) -> str:
        return f"{self.root_dir}/{self.mqtt_root_pem_path}"

    @property
    def config_file_absolute_path(self) -> str:
        return f"{self.root_dir}/{self.config_file_path}"

    @property
    def logging_file_absolute_path(self) -> str:
        return f"{self.root_dir}/{self.logging_file_path}"

    @property
    def dry_config_file_absolute_path(self) -> str:
        return f"{self.root_dir}/{self.dry_config_file_path}"

    @property
    def screen_update_interval(self) -> float:
        return self.screenUpdateInterval

    @property
    def event_sync_interval(self) -> float:
        return self.eventSyncInterval

    @property
    def state_sync_interval(self) -> float:
        return self.stateSyncInterval

    @property
    def full_sqlite_path(self) -> str:
        # If the path starts with 'tmp', this means we want to run the database in a tmpfs memory directory,
        # and since /tmp is mounted as tmpfs, we use this
        if self.sqlitePath.startswith("tmp"):
            return f"sqlite:////{self.sqlitePath}"

        if self.sqlitePath != '':
            ret = f"sqlite:///{self.root_dir}/{self.sqlitePath}"
        else:
            ret = "sqlite:///:memory:"

        return ret

    @property
    def mqtt_event_topic(self) -> str:
        ret = None
        if self.deviceId != '' and self.projectId != '':
            ret = f"dt{self.topicPrefix}projects/{self.projectId}/devices/{self.deviceId}/events"

        return ret

    @property
    def mqtt_count_topic(self) -> str:
        ret = None
        if self.projectId != '':
            ret = f"dt/projects/{self.projectId}/counting"

        return ret

    @property
    def mqtt_config_topic(self) -> str:
        ret = None
        if self.deviceId != '':
            ret = f"cfg/devices/{self.deviceId}"

        return ret

    @property
    def mqtt_cmd_topic(self):
        ret = None
        if self.projectId != '':
            ret = f"cmd{self.topicPrefix}projects/{self.projectId}/devices/{self.deviceId}"

        return ret

    @property
    def mqtt_state_topic(self) -> str:
        ret = None
        if self.deviceId != '' and self.projectId != '':
            ret = f"dt{self.topicPrefix}projects/{self.projectId}/devices/{self.deviceId}/state"

        return ret

    @property
    def mqtt_log_topic(self) -> str:
        ret = None
        if self.deviceId != '' and self.projectId != '':
            ret = f"dt{self.topicPrefix}projects/{self.projectId}/devices/{self.deviceId}/logs"

        return ret

    def update_config_with_dict(self, config_dict: Dict):
        """
        Update the config file with the JSON dict received
        :param config_dict:
        :return: None
        """

        for key in self.__dict__.keys():
            if key in config_dict.keys():
                if config_dict[key] is not None and config_dict[key] != '' or \
                        key == 'updateBranch' or \
                        key == 'sqlitePath':
                    self.__dict__[key] = config_dict[key]

        self.write_config_to_file()

    def write_config_to_file(self):
        """
        Save current config to file
        :return: None
        """
        with open(self.config_file_absolute_path, 'w+') as f:
            json.dump(self.__dict__, f)

    def load_config_from_file(self, file_path: str) -> bool:
        """
        Load config parameters from file
        :param file_path: path to config file
        :return: True if file exists
        """
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                config_dict = json.load(f)

                for key in self.__dict__.keys():
                    if key in config_dict.keys():
                        self.__dict__[key] = config_dict[key]

                return True
        else:
            return False


cfg = Config()
