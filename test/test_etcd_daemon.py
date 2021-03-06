#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2020 SBofGaySchoolBuPaAnything
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

__author__ = "chenty"

# Add current folder and parent folder into python path
import os
os.environ["PYTHONPATH"] = os.environ.get("PYTHONPATH", "") + ":" + os.getcwd()
os.environ["PYTHONPATH"] += ":" + os.path.dirname(os.getcwd())
import sys
sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(os.getcwd()))
import unittest
import multiprocessing
import signal
import time
import shutil
import tracemalloc
import json
tracemalloc.start()

from utility.etcd.daemon import run
from utility.etcd.proxy import EtcdProxy
from utility.function import get_logger


# Unit test class for utility.etcd.daemon
class TestEtcdDaemon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Initialization function
        :return: None
        """
        print("Initializing environment.\n")
        # Generate temp dirs
        for d in ["etcd1", "etcd2", "etcd3", "etcd4"]:
            os.mkdir(d)
            for sd in ["etcd", "etcd_init"]:
                os.mkdir(d + "/" + sd)

        # Generate configuration files
        with open("etcd1/conf.json", "w") as f:
            f.write(json.dumps({
                "daemon": {
                    "retry": {
                        "times": 3,
                        "interval": 5
                    },
                    "raw_log_symbol_pos": 27,
                },
                "etcd": {
                    "exe": "etcd",
                    "name": "etcd1",
                    "data_dir": "etcd1/etcd",
                    "data_init_dir": "etcd1/etcd_init",
                    "listen": {
                        "address": "0.0.0.0",
                        "peer_port": "2000",
                        "client_port": "2001"
                    },
                    "advertise": {
                        "address": "localhost",
                        "peer_port": "2000",
                        "client_port": "2001"
                    },
                    "cluster": {
                        "type": "init"
                    }
                }
            }, indent=4))
        with open("etcd2/conf.json", "w") as f:
            f.write(json.dumps({
                "daemon": {
                    "retry": {
                        "times": 3,
                        "interval": 5
                    },
                    "raw_log_symbol_pos": 27,
                },
                "etcd": {
                    "exe": "etcd",
                    "name": "etcd2",
                    "data_dir": "etcd2/etcd",
                    "data_init_dir": "etcd2/etcd_init",
                    "listen": {
                        "address": "0.0.0.0",
                        "peer_port": "2002",
                        "client_port": "2003"
                    },
                    "advertise": {
                        "address": "localhost",
                        "peer_port": "2002",
                        "client_port": "2003"
                    },
                    "cluster": {
                        "type": "join",
                        "client": "http://localhost:2001"
                    }
                }
            }, indent=4))
        with open("etcd3/conf.json", "w") as f:
            f.write(json.dumps({
                "daemon": {
                    "retry": {
                        "times": 3,
                        "interval": 5
                    },
                    "raw_log_symbol_pos": 27,
                },
                "etcd": {
                    "exe": "etcd",
                    "name": "etcd3",
                    "data_dir": "etcd3/etcd",
                    "data_init_dir": "etcd3/etcd_init",
                    "listen": {
                        "address": "0.0.0.0",
                        "peer_port": "2004",
                        "client_port": "2005"
                    },
                    "advertise": {
                        "address": "localhost",
                        "peer_port": "2004",
                        "client_port": "2005"
                    },
                    "cluster": {
                        "type": "join",
                        "client": "http://localhost:2001"
                    }
                }
            }, indent=4))
        with open("etcd4/conf.json", "w") as f:
            f.write(json.dumps({
                "daemon": {
                    "retry": {
                        "times": 3,
                        "interval": 5
                    },
                    "raw_log_symbol_pos": 27,
                },
                "etcd": {
                    "exe": "etcd",
                    "name": "etcd4",
                    "data_dir": "etcd4/etcd",
                    "data_init_dir": "etcd4/etcd_init",
                    "listen": {
                        "address": "0.0.0.0",
                        "peer_port": "2006",
                        "client_port": "2007"
                    },
                    "advertise": {
                        "address": "localhost",
                        "peer_port": "2006",
                        "client_port": "2007"
                    },
                    "proxy": "on",
                    "cluster": {
                        "type": "join",
                        "client": "http://localhost:2001"
                    }
                }
            }, indent=4))


        # Sub processes
        cls.etcd1 = None
        cls.etcd2 = None
        cls.etcd3 = None
        cls.etcd4 = None
        return

    def test_000_run_etcd_daemon(self):
        """
        Test to run etcd through etcd daemon
        :return: None
        """
        cls = self.__class__

        # Generate all daemon
        cls.etcd1 = multiprocessing.Process(target=run, args=("Etcd1", "etcd1/conf.json"))
        cls.etcd1.daemon = True
        cls.etcd1.start()
        time.sleep(2)
        cls.etcd4 = multiprocessing.Process(target=run, args=("Etcd4", "etcd4/conf.json"))
        cls.etcd4.daemon = True
        cls.etcd4.start()
        time.sleep(2)
        cls.etcd2 = multiprocessing.Process(target=run, args=("Etcd2", "etcd2/conf.json"))
        cls.etcd2.daemon = True
        cls.etcd2.start()
        cls.etcd3 = multiprocessing.Process(target=run, args=("Etcd3", "etcd3/conf.json"))
        cls.etcd3.daemon = True
        cls.etcd3.start()

        time.sleep(20)

        # Test if every etcd has joined the cluster
        proxy = EtcdProxy("http://localhost:2001", get_logger("Test", None, None))
        self.assertEqual(
            proxy.add_and_get_members(None, None),
            {"etcd1": "http://localhost:2000", "etcd2": "http://localhost:2002", "etcd3": "http://localhost:2004"}
        )
        proxy.set("key", "value")
        self.assertEqual(proxy.get("key"), "value")
        return

    def test_001_stop_etcd_daemon(self):
        """
        Test to stop etcd through daemon
        :return: None
        """
        cls = self.__class__
        proxy = EtcdProxy("http://localhost:2005", get_logger("Test", None, None))

        os.kill(cls.etcd1.pid, signal.SIGINT)
        cls.etcd1.join()
        time.sleep(10)
        self.assertEqual(
            proxy.add_and_get_members(None, None),
            {"etcd2": "http://localhost:2002", "etcd3": "http://localhost:2004"}
        )

        os.kill(cls.etcd2.pid, signal.SIGINT)
        cls.etcd2.join()
        time.sleep(10)
        self.assertEqual(
            proxy.add_and_get_members(None, None),
            {"etcd3": "http://localhost:2004"}
        )

        return

    @classmethod
    def tearDownClass(cls):
        """
        Cleaning function
        :return: None
        """
        print("Tearing down environment.\n")

        # Stop subprocess
        if cls.etcd1 and cls.etcd1.is_alive():
            if cls.etcd1.pid:
                os.kill(cls.etcd1.pid, signal.SIGINT)
            cls.etcd1.join()
        if cls.etcd2 and cls.etcd2.is_alive():
            if cls.etcd2.pid:
                os.kill(cls.etcd2.pid, signal.SIGINT)
            cls.etcd2.join()
        if cls.etcd3 and cls.etcd3.is_alive():
            if cls.etcd3.pid:
                os.kill(cls.etcd3.pid, signal.SIGINT)
            cls.etcd3.join()
        if cls.etcd4 and cls.etcd4.is_alive():
            if cls.etcd4.pid:
                os.kill(cls.etcd4.pid, signal.SIGINT)
            cls.etcd4.join()

        # Remove temp dir
        for d in ["etcd1", "etcd2", "etcd3", "etcd4"]:
            shutil.rmtree(d)
        return

if __name__ == "__main__":
    unittest.main()
