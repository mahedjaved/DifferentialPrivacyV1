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
    FakeAPI = "/users"  # This is now a relative path
    CryptoWallet = "/api/v1/register"  # This is also a relative path


class WebsiteUser(HttpUser):
    wait_time = between(1, 2)
    host = "https://fake-json-api.mock.beeceptor.com"  # Base URL for the tests

    @task
    def GET_USERS(self):
        response = self.client.get(URLS.FakeAPI)  # Use relative URL, not full URL
        if response.status_code == 400:
            print(f"Error encountered for {self.__class__.__name__}:", response.text)


# Function to manage user load dynamically
def manage_user_load(env, total_runtime, base_user_count=50, peak_user_count=200, ramp_up_interval=5, peak_duration=1):
    """
    Manages user load dynamically based on the specified pattern.
    """
    current_user_count = base_user_count
    spawn_rate = base_user_count / ramp_up_interval  # Control the rate of spawning users
    env.runner.start(current_user_count, spawn_rate)
    print(f"Starting with {current_user_count} users")

    # After total time is done, drop users back to the base count
    if current_user_count > base_user_count:
        env.runner.start(base_user_count - current_user_count, spawn_rate)
        current_user_count = base_user_count
        print(f"Reducing to base count: {current_user_count} users")


# Function to run Locust test programmatically for a fixed duration
def run_locust_test(user_count, spawn_rate, run_time=5):
    """
    Runs the Locust test programmatically for a fixed duration.
    """
    # Set up Locust environment
    env = Environment(user_classes=[WebsiteUser], events=events)
    env.create_local_runner()

    # Start stats printing and history recording
    gevent.spawn(stats_printer, env.stats)
    gevent.spawn(stats_history, env.runner)

    # Start Web UI (optional, for debugging purposes)
    web_ui = env.create_web_ui("127.0.0.1", 8089)

    # Variables to collect RPS data
    rps_data = []
    users_data = []
    avgresptime_data = []

    # Manage user load for the total runtime of the test
    total_runtime = 5 * 60  # 5 minutes
    manage_user_load(env, total_runtime)

    # Capture RPS data every second for 5 minutes
    start_time = time.time()
    while time.time() - start_time < total_runtime:
        current_rps = env.stats.total.current_rps
        current_user = env.runner.user_count
        current_avgresptime = env.stats.total.avg_response_time
        rps_data.append(current_rps)
        users_data.append(current_user)
        avgresptime_data.append(current_avgresptime)
        plot_metrics(rps_data, avgresptime_data, users_data)
        gevent.sleep(1)  # Capture RPS every 1 second

    # Stop the Locust runner after the total runtime
    env.runner.stop()
    while env.runner.state != 'STOPPED':
        gevent.sleep(0.1)

    # Stop Web UI if started
    if hasattr(env, "web_ui"):
        env.web_ui.stop()

    # # Plot RPS data in the main thread to avoid blocking
    # plot_rps_data(rps_data)  # Call the plot function directly here to ensure it waits
    # return rps_data


# Separate function for plotting
def plot_metrics(rps_data, response_times, active_user_counts):
    plt.subplot(3, 1, 1)
    plt.plot(rps_data, label="RPS", color='b')
    plt.xlabel("Time (seconds)")
    plt.ylabel("Requests per Second (RPS)")
    plt.title("Requests Per Second (RPS) Over Time")
    plt.legend(loc="upper right")

    # Plot Average Response Time in the second subplot
    plt.subplot(3, 1, 2)
    plt.plot(response_times, label="Avg Response Time", color='g')
    plt.xlabel("Time (seconds)")
    plt.ylabel("Response Time (ms)")
    plt.title("Average Response Time Over Time")
    plt.legend(loc="upper right")

    # Plot Number of Active Users in the third subplot
    plt.subplot(3, 1, 3)
    plt.plot(active_user_counts, label="Active Users", color='r')
    plt.xlabel("Time (seconds)")
    plt.ylabel("Number of Active Users")
    plt.title("Number of Active Users Over Time")
    plt.legend(loc="upper right")

    # Adjust the layout to prevent overlap
    plt.tight_layout()

    # Show the plot
    plt.show(block=True)


if __name__ == "__main__":
    # Running the test
    user_count = 50
    spawn_rate = 1
    run_time = 5  # Run time in seconds
    rps_data = run_locust_test(user_count, spawn_rate, run_time=run_time)
