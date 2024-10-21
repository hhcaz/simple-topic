import time


class Rate(object):
    def __init__(self, hz: float):
        self.hz = hz
        self.dt = 1.0 / hz
        self.last_sleep = None
        self.short_sleep_thresh = 1e-4
    
    def __sleep(self, current: float, to_sleep: float):
        if to_sleep > self.short_sleep_thresh:
            time.sleep(to_sleep)
            last_sleep = current + max(to_sleep, 0)
        else:
            desired = current + to_sleep
            while current < desired:
                current = time.perf_counter()
            last_sleep = max(current, desired)
        return last_sleep
    
    def sleep(self):
        if self.last_sleep is None:
            self.last_sleep = time.perf_counter()
        else:
            current = time.perf_counter()
            to_sleep = self.dt - (current - self.last_sleep)
            self.last_sleep = self.__sleep(current, to_sleep)

