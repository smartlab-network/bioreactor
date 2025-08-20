import json
from contextlib import contextmanager
from threading import Lock
from typing import Iterator
from tkinter import messagebox


@contextmanager
def lock_threading_lock(lock: Lock, *, timeout: float) -> Iterator[None]:
    """Context manager for using a `threading.lock` with a timeout"""
    if not timeout > 0:
        raise ValueError("Timeout must be positive")

    if not lock.acquire(timeout=timeout):
        raise TimeoutError(f"Could not acquire lock after {timeout} seconds")

    try:
        yield
    finally:
        lock.release()

def read_json() -> dict:
    with open('setup.json', 'r', encoding='utf-8') as file:
        contents = json.load(file)
    return contents

def write_json(parameter: str, value: any) -> None:
    data = read_json()
    data[parameter] = value
    with open('setup.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def message_box_error(error: str):
    if error == "not found":
        messagebox.showerror("SerialException", "COM port does not exist. Please choose the correct one.")

    elif error == "no permission":
        messagebox.showerror("SerialException", "Current selected port is occupied")

    elif error == "wrong pins":
        messagebox.showerror("Input Error", "all pins must be integers")

    elif error == "unexpected error":
        messagebox.showerror("SerialException", "Something went wrong")

    elif error == "wrong prescale":
        messagebox.showerror("InputError", "prescale must be an integer")