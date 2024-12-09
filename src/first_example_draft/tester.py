from locust import HttpUser, between, constant, constant_pacing, constant_throughput, task
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
from locust.runners import STATE_STOPPED
import gevent
import time


class URLS:
    FakeAPI = "https://fake-json-api.mock.beeceptor.com"
    CryptoWallet = "https://crypto-wallet-server.mock.beeceptor.com"


class Endpoints:
    # For the FakeAPI
    Users = "/users"  # Returns a list of ten users in JSON format. Every time you hit this, you get a new set
    Companies = "/companies"  # Get a list of ten random companies
    # for CryptoWallet API
    CreateRegister = "/api/v1/register"
    CreateLogin = "api/v1/login"
    GetBalance = "api/v1/balance"
    GetAllTransactions = "api/v1/transactions"
    GetAllExchangeRates = "api/v1/exchange_rates"


class WebsiteUser(HttpUser):
    wait_time = between(1, 2)


@task
def GET_USERS(self):
    # with self.client.post(URLS.FakeAPI + Endpoints.Users, ) as response:
    response = self.client.get(URLS.FakeAPI + Endpoints.Users)
    if response.status_code in [200, 201]:
        print(f"Request successful, output : {response.json()}")
    elif response.status_code == 400:
        print(f"Error encountered for {self.__name__}:", response.text)


# Set up Locust environment
env = Environment(user_classes=[WebsiteUser])
env.create_local_runner()
env.create_web_ui("127.0.0.1", 8089)  # Optional: Enable the Web UI for debugging

# Start Locust runner
env.runner.start(user_count=10, spawn_rate=1)
gevent.spawn(stats_printer(env.stats))  # Print stats to console
gevent.spawn(stats_history, env.runner)  # Store stats history

# Run for the specified time
time.sleep(run_time=5)

# Stop Locust runner
env.runner.quit()
env.web_ui.stop()

# Return performance metrics (throughput in this case)
total_rps = env.stats.total.get_response_time_percentile(50)  # Median response time
print(f"Throughput (median response time): {total_rps}")


# Function to run Locust test
def run_locust_test(user_count, spawn_rate, run_time=5):
    """
    Runs the Locust test programmatically for a fixed duration.
    """
    setup_logging("INFO", None)  # Optional: Enables Locust logging

    # Set up Locust environment
    env = Environment(user_classes=[WebsiteUser])
    env.create_local_runner()

    # Start the Locust runner
    env.runner.start(user_count=user_count, spawn_rate=spawn_rate)

    # Start stats printing and history recording
    gevent.spawn(stats_printer(env.stats))
    gevent.spawn(stats_history, env.runner)

    # Run for the specified time
    gevent.sleep(run_time)

    # Stop the Locust runner
    env.runner.stop()
    while env.runner.state != STATE_STOPPED:
        gevent.sleep(0.1)

    # Stop Web UI if started
    if hasattr(env, "web_ui"):
        env.web_ui.stop()

    # Collect performance metrics
    total_rps = env.stats.total.current_rps  # Requests per second
    median_response_time = env.stats.total.get_response_time_percentile(50)
    print(f"Throughput (RPS): {total_rps}, Median Response Time: {median_response_time}")
    return total_rps
