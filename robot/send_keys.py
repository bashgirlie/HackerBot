#!/usr/bin/env python3


import socket
from pynput import keyboard
import asyncio

"""
Script to take key inputs from a laptop pynput, encode and send them as useful data to a robot via UDP with sockets while the robot is in AP mode (which the laptop connects to).
"""


encode_keys = {
    "w": "forward",
    "a": "left",
    "s": "reverse",
    "d": "right",
    keyboard.Key.space: "stop",
}

COMBINATIONS = [
    {keyboard.Key.ctrl_l, keyboard.KeyCode(char='c')},
    {keyboard.Key.ctrl_r, keyboard.KeyCode(char='c')}
]

# Track currently active keys
currently_pressed = set()
last_sent_command = None

# create queue
event_queue = asyncio.Queue()
async_loop = None

def start_keyboard_listener():
    """Starts the synchronous pynput listener loop."""
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def on_press(key):
    global async_loop, last_sent_command
    try:
        currently_pressed.add(key)

        #check for exit combination first
        for combination in COMBINATIONS:
            if combination.issubset(currently_pressed):
                print(f"[+] CTRL+C detected! Exiting cleanly...")
                if async_loop:
                    #inject exit token into event loop
                    async_loop.call_soon_threadsafe(event_queue.put_nowait, "EXIT")
                return False # stop listener
    
        key_lookup = key.char if hasattr(key, 'char') and key.char is not None else key
        if key_lookup in encode_keys and async_loop:
            command = encode_keys[key_lookup]

            # debounce; only queue command if it changes from previous
            if command != last_sent_command:
                print(f"[+] Key {key_lookup} pressed -> Queueing: {command}")
                last_sent_command = command
                # push command from pynput thread to ayncio thread
                async_loop.call_soon_threadsafe(event_queue.put_nowait, command)
            
    except Exception as e:
        print(f"[!] Error handling input {e}.")

def on_release(key):
    global async_loop, last_sent_command
    try:
        currently_pressed.remove(key)
    except KeyError:
        pass

    try:
        key_lookup = key.char if hasattr(key, 'char') and key.char is not None else key

        if key_lookup in encode_keys and async_loop:
            last_sent_command = None
            print(f"[+] Key {key_lookup} released -> Queueing: stop")
            async_loop.call_soon_threadsafe(event_queue.put_nowait, "stop")
    except Exception as e:
        print(f"[!] Error handling release input: {e}")
    

async def send_udp_worker(server_destination):
    """Asynchronous worker that pulls from the queue and handles socket transmission."""
    #create udp socket AF_INET = IPv4, SOCK_DGRAM = UDP
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setblocking(False)
        udp_socket.connect(server_destination) # fake, but increases speed and prevents issues with sendto
        print(f"[+] UDP worker active. Target: {server_destination}")

        while True:
            command = await event_queue.get()
            if command == "EXIT":
                udp_socket.send(b"stop")
                event_queue.task_done()
                break

            encoded_data = command.encode('utf-8')
            await async_loop.sock_send(udp_socket, encoded_data)
            event_queue.task_done()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 6. Clean up and close the socket
        udp_socket.close()
        print("Socket closed.")

async def main():
    global async_loop

    async_loop = asyncio.get_running_loop()

    # server setup
    SERVER_IP = "127.0.0.1" # replace with real
    SERVER_PORT = 5005 # not commonly used
    server_destination = (SERVER_IP, SERVER_PORT)

    # run synchronous pynput listener inside executor pool to prevent blocking async loop
    listener_task = async_loop.run_in_executor(None, start_keyboard_listener)

    # run UDP transmission worker
    worker_task = asyncio.create_task(send_udp_worker(server_destination))
    # run until UDP worker finishes
    await worker_task
    print(f"[*] Main event loop finished.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    print(f"[+] Program successfully exited.")
    
    
    
    
