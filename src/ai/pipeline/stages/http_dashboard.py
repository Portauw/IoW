import json
import requests
from src.ai.pipeline.stages import PipelineStage


class HttpDashboard(PipelineStage):
    """
     Http dashboard
    """

    def __init__(self, username, password, **kwargs):
        """
        Constructor method

        :param username: username for login on dashboard
        :type username: string
        :param password: password for login on dashboard
        :type password: string
        """
        super().__init__(prefix="HT ", **kwargs)
        self.temp_in = 0
        self.temp_out = 0
        self.login_url = 'https://api-dot-edgise-coronos-telling.appspot.com/api/Locations/loginAndGet'
        self.increase_url = 'https://api-dot-edgise-coronos-telling.appspot.com/api/Stats/increase'
        self.decrease_url = 'https://api-dot-edgise-coronos-telling.appspot.com/api/Stats/decrease?'
        self.get_state_url = 'https://api-dot-edgise-coronos-telling.appspot.com/api/Stats/getStatOfToday'
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        }
        self.data_auth = {
            'username': username,
            'password': password
        }
        self.login_data = {}
        self.login(self.login_url)
        self.params_location = (
            ('locationId', self.login_data['location']['id']),
            ('access_token', self.login_data['login']['id']),
        )
        self.params = (
            ('access_token', self.login_data['login']['id']),
        )

    def __call__(self, input_data, *args, **kwargs):
        """
        Invoke interpreter

        :param input_data: the output from the previous stage
        :type input_data: str
        """
        self.get_numbers_from_output(input_data)

    def __str__(self):
        """
        Returns all the dashboard data

        :return: current dashboard data
        """
        current_stats = self.get_current_state()
        return f"Dashboard data:{current_stats}"

    def get_numbers_from_output(self, input_data):
        """
        Get numbers from the input string and in- or decrease accordingly

        :param input_data: data from previous STT stage
        :type input_data: str
        """
        numbers = [int(number) for number in input_data.split() if number.isdigit()]
        amount_in = numbers[0]
        amount_out = numbers[1]
        if amount_in > self.temp_in:
            self.increase(amount_in - self.temp_in)
            self.temp_in = amount_in
        if amount_out > self.temp_out:
            self.decrease(amount_out - self.temp_out)
            self.temp_out = amount_out

    def get_current_state(self):
        """
        Returns the current statistics of the dashboard.
        """
        params = (
            ('locationId', self.login_data['location']['id']),
            ('access_token', self.login_data['login']['id']),
        )
        get_current_state = requests.get(self.get_state_url, headers=self.headers, params=params)
        if get_current_state.status_code == 200 or 204:
            print("Get state: Code: {} Response: {}".format(get_current_state.status_code, get_current_state.text))
            return get_current_state.text

    def login(self, url):
        """
        Login with username and password

        :param url: login url of the dashboard
        :type url: str
        """
        login_response = requests.post(url, headers=self.headers, data=self.data_auth)
        if login_response.status_code == 200 or 204:
            self.login_data = json.loads(login_response.text)
            return print(
                '''
                Login id: {}
                Location name: {}
                Location id: {}
                Current statistics: {}
                '''.format(self.login_data['login']['id'], self.login_data['location']['name'],
                           self.login_data['location']['id'], self.login_data['statOfToday']['stat']))
        else:
            return print("Something went wrong with status code: {}".format(login_response.status_code))

    def increase(self, amount):
        """
        Increases the amount of people in the building.

        :param amount: how many people should be counted per detection
        :type amount: int
        """
        data = {
            'locationId': self.login_data['location']['id'],
            'count': amount
        }
        increase_response = requests.post(self.increase_url, headers=self.headers, params=self.params_location,
                                          data=data)
        # increase_response_text = json.loads(increase_response.text)
        # print("Actual: {}".format(increase_response_text))

        if increase_response.status_code == 200 or 204:
            return print(
                "Increase: Code: {} Response: {}".format(increase_response.status_code, increase_response.text))
        else:
            return print("Something went wrong with status code: {}".format(increase_response.status_code))

    def decrease(self, amount):
        """
        Decreases the amount of people in the building.

        :param amount: how many people should be counted per detection
        :type amount: int
        """
        data = {
            'locationId': self.login_data['location']['id'],
            'count': amount
        }
        decrease_response = requests.post(self.decrease_url, headers=self.headers, params=self.params_location,
                                          data=data)

        if decrease_response.status_code == 200 or 204:
            return print(
                "Decrease: Code: {} Response: {}".format(decrease_response.status_code, decrease_response.text))
        else:
            return print("Something went wrong with status code: {}".format(decrease_response.status_code))


##################################
# BELOW CODE IS ONLY FOR TESTING #
##################################
if __name__ == '__main__':
    dashboard = HttpDashboard('test', 'test')
    dashboard.increase(0)
    dashboard.get_current_state()
    dashboard.decrease(0)
    dashboard.get_current_state()
