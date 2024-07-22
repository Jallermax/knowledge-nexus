from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

colorama_init()

def print_colored_text_same_line(text, color = Fore.CYAN):
    print(f"{color}{text}{Style.RESET_ALL}\r", end = "")
