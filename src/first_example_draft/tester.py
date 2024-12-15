import time
import gevent
import matplotlib.pyplot as plt
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging

setup_logging("INFO")

# Define the URLs and Endpoints
class URLS:
    FakeAPI = "https://fake-json-api.mock.beeceptor.com"
    CryptoWallet = "https://crypto-wallet-server.mock.beeceptor.com"

class Endpoints:
    # For the FakeAPI
    Users = "/users"  # Returns a list of ten users in JSON format. Every time you hit this, you get a new set
    Companies = "/companies"  # Get a list of ten random companies
    # For CryptoWallet API
    CreateRegister = "/api/v1/register"
    CreateLogin = "/api/v1/login"
    GetBalance = "/api/v1/balance"
    GetAllTransactions = "/api/v1/transactions"
    GetAllExchangeRates = "/api/v1/exchange_rates"

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)
    host = "https://fake-json-api.mock.beeceptor.com"  # Base URL for the tests

    @task
    def GET_USERS(self):
        response = self.client.get(URLS.FakeAPI + Endpoints.Users)
        if response.status_code in [200, 201]:
            print(f"Request successful, output : {response.json()}")
        elif response.status_code == 400:
            print(f"Error encountered for {self.__class__.__name__}:", response.text)


# Function to run Locust test programmatically for a fixed duration
def run_locust_test(user_count, spawn_rate, run_time=5):
    """
    Runs the Locust test programmatically for a fixed duration.
    """
    # Set up Locust environment
    env = Environment(user_classes=[WebsiteUser], events=events)
    env.create_local_runner()

    # Start the Locust runner
    env.runner.start(user_count=user_count, spawn_rate=spawn_rate)

    # Start stats printing and history recording
    gevent.spawn(stats_printer(env.stats))
    gevent.spawn(stats_history, env.runner)

    # Start Web UI (optional, for debugging purposes)
    web_ui = env.create_web_ui("127.0.0.1", 8089)

    # Variables to collect RPS data
    rps_data = []

    # Run for the specified time
    start_time = time.time()
    while time.time() - start_time < run_time:
        # Capture RPS every 1 second
        current_rps = env.stats.total.current_rps
        rps_data.append(current_rps)
        gevent.sleep(1)

    # Stop the Locust runner
    env.runner.stop()
    while env.runner.state != 'STOPPED':
        gevent.sleep(0.1)

    # Stop Web UI if started
    if hasattr(env, "web_ui"):
        env.web_ui.stop()

    # Plot RPS data in the main thread to avoid blocking
    gevent.spawn(lambda: plot_rps_data(rps_data))

    return rps_data


# Separate function for plotting
def plot_rps_data(rps_data):
    plt.plot(rps_data, label="RPS")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Requests per Second (RPS)")
    plt.title("Requests Per Second (RPS) Over Time")
    plt.legend()
    plt.show(block=True)  # Ensure plt.show() is blocking to allow proper window display


if __name__ == "__main__":
    # Running the test
    user_count = 10
    spawn_rate = 1
    run_time = 5  # Run time in seconds
    rps_data = run_locust_test(user_count, spawn_rate, run_time)

    print(rps_data)
