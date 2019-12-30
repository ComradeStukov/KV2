# -*- encoding: utf-8 -*-

__author__ = "chenty"


# Status of a task
TASK_STATUS = {
    "UNKNOWN_ERROR": -1,
    "PENDING": 0,
    "COMPILING": 1,
    "COMPILE_FAILED": 2,
    "RUNNING": 3,
    "RUN_FAILED": 4,
    "SUCCESS": 5,
    "RETRYING": 6,
    "CANCELLED": 7
}