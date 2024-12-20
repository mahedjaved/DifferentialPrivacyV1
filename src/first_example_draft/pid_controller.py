import time
import gevent
import matplotlib.pyplot as plt
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
from collections import deque
import numpy as np

setup_logging("INFO")


# Define the URLs and Endpoints
class URLS:
    FakeAPI = "/users"
    CryptoWallet = "/api/v1/register"


class WebsiteUser(HttpUser):
    wait_time = between(1, 2)
    host = "https://fake-json-api.mock.beeceptor.com"

    @task
    def GET_USERS(self):
        response = self.client.get(URLS.FakeAPI)
        if response.status_code == 400:
            print(f"Error encountered for {self.__class__.__name__}:", response.text)


# Set max length for the data collection (for example, 300 seconds)
MAX_LENGTH = 300
rps_data = deque(maxlen=MAX_LENGTH)
users_data = deque(maxlen=MAX_LENGTH)
avgresptime_data = deque(maxlen=MAX_LENGTH)

# PID controller constants
Kp = 0.1  # Proportional constant
Ki = 0.01  # Integral constant
Kd = 0.05  # Derivative constant

# Initialize PID variables
previous_error = 0
integral = 0


# Function to calculate moving average
def moving_average(data, window_size=30):
    return np.mean(data[-window_size:]) if len(data) >= window_size else np.mean(data)


def pid_control(target_rps, current_rps, previous_error, integral, dt=1):
    # Calculate error
    error = target_rps - current_rps

    # Calculate integral (sum of past errors)
    integral += error * dt

    # Calculate derivative (rate of change of the error)
    derivative = (error - previous_error) / dt

    # Calculate the PID output
    output = Kp * error + Ki * integral + Kd * derivative

    # Return the output and updated values
    return output, error, integral


def manage_user_load_with_pid(env, target_rps=40, user_step=10, dt=1):
    global previous_error, integral

    # Get current RPS
    current_rps = env.stats.total.current_rps

    # Apply PID control to get the number of users to spawn
    pid_output, previous_error, integral = pid_control(target_rps, current_rps, previous_error, integral, dt)

    # Calculate new user count based on PID output (making sure we don't go below a minimum number)
    new_user_count = max(10, int(env.runner.user_count + pid_output))  # Ensuring we don't go below 10 users

    print(f"PID Control Output: {pid_output}, Adjusting users to {new_user_count}")

    # Start or stop users to match the target RPS
    env.runner.start(new_user_count, new_user_count)


def plot_metrics__(avgresptime_data, env, rps_data, users_data, total_runtime=5 * 60):
    current_rps = env.stats.total.current_rps
    current_user = env.runner.user_count
    current_avgresptime = env.stats.total.avg_response_time
    rps_data.append(current_rps)
    users_data.append(current_user)
    avgresptime_data.append(current_avgresptime)

    # Plot the metrics
    plot_metrics(rps_data, avgresptime_data, users_data)
    gevent.sleep(1)  # Capture RPS every 1 second


def plot_metrics(rps_data, response_times, active_user_counts):
    plt.subplot(3, 1, 1)
    plt.plot(rps_data, label="RPS", color='b')
    plt.xlabel("Time (seconds)")
    plt.ylabel("Requests per Second (RPS)")
    plt.title("Requests Per Second (RPS) Over Time")
    plt.legend(loc="upper right")

    plt.subplot(3, 1, 2)
    plt.plot(response_times, label="Avg Response Time", color='g')
    plt.xlabel("Time (seconds)")
    plt.ylabel("Response Time (ms)")
    plt.title("Average Response Time Over Time")
    plt.legend(loc="upper right")

    plt.subplot(3, 1, 3)
    plt.plot(active_user_counts, label="Active Users", color='r')
    plt.xlabel("Time (seconds)")
    plt.ylabel("Number of Active Users")
    plt.title("Number of Active Users Over Time")
    plt.legend(loc="upper right")

    plt.tight_layout()
    plt.show(block=True)


def run_locust_test():
    env = Environment(user_classes=[WebsiteUser], events=events)
    env.create_local_runner()

    gevent.spawn(stats_printer, env.stats)
    gevent.spawn(stats_history, env.runner)

    web_ui = env.create_web_ui("127.0.0.1", 8089)

    total_runtime = 5 * 60
    start_time = time.time()
    env.runner.start(50, 50)
    print("Starting with 50 users")

    while time.time() - start_time < total_runtime:
        manage_user_load_with_pid(env)
        plot_metrics__(avgresptime_data, env, rps_data, users_data)

    env.runner.stop()
    while env.runner.state != 'STOPPED':
        gevent.sleep(0.1)

    if hasattr(env, "web_ui"):
        env.web_ui.stop()


if __name__ == "__main__":
    run_locust_test()
