import sys
import time
import logging
from threading import Thread, Event


class LoggingProgressBar:
    def __init__(self, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.print_end = print_end
        self.iteration = 0
        self.logger = logging.getLogger(__name__)
        self._stop_event = Event()
        self._progress_thread = None

    def update(self):
        self.iteration += 1
        self._print_progress_bar()

    def start(self):
        self._progress_thread = Thread(target=self._progress_loop)
        self._progress_thread.start()

    def finish(self):
        self._stop_event.set()
        if self._progress_thread:
            self._progress_thread.join()
        self._print_progress_bar()
        print()  # Move to the next line after completion

    def _progress_loop(self):
        while not self._stop_event.is_set():
            self._print_progress_bar()
            time.sleep(0.5)  # Update every half second

    def _print_progress_bar(self):
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.iteration / float(self.total)))
        filled_length = int(self.length * self.iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        progress_bar = f'\r{self.prefix} |{bar}| {percent}% {self.suffix}'

        # Clear the current line and print the progress bar
        sys.stdout.write('\033[K')  # Clear to the end of line
        sys.stdout.write(progress_bar)
        sys.stdout.flush()


# Custom logging handler to work with the progress bar
class ProgressBarHandler(logging.Handler):
    def __init__(self, progress_bar):
        super().__init__()
        self.progress_bar = progress_bar

    def emit(self, record):
        # Clear the current line (progress bar)
        sys.stdout.write('\033[K')

        # Print the log message
        print(self.format(record))

        # Redraw the progress bar
        self.progress_bar._print_progress_bar()


# Usage example
def process_pages(total_pages):
    logger = logging.getLogger(__name__)
    progress_bar = LoggingProgressBar(total_pages, prefix='Processing:', suffix='Complete', length=50)

    # Add the custom handler
    handler = ProgressBarHandler(progress_bar)
    logger.addHandler(handler)

    progress_bar.start()

    for i in range(total_pages):
        # Simulate some work
        time.sleep(0.1)

        # Log some messages occasionally
        if i % 10 == 0:
            logger.info(f"Processed page group {i // 10}")

        progress_bar.update()

    progress_bar.finish()

    # Remove the custom handler
    logger.removeHandler(handler)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    process_pages(100)