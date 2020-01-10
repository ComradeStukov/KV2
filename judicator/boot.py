# -*- encoding: utf-8 -*-

__author__ = "chenty"

# Add current folder and parent folder (when testing) into python path
import os
os.environ["PYTHONPATH"] += ":" + os.getcwd()
os.environ["PYTHONPATH"] += ":" + os.path.dirname(os.getcwd())

from jsoncomment import JsonComment
json_comment = JsonComment()

import json
import time
import fcntl
import errno
import subprocess
import argparse
import socket
import docker
import signal

from utility.function import get_logger, transform_address


def handler(signum, frame):
    """
    Signal handler of SIGTERM. Sending SIGINT to this process
    :param signum: Unused, signal number
    :param frame: Unused
    :return: None
    """
    logger.info("Received SIGTERM. Sending SIGINT to self.")
    # Send signal
    os.kill(os.getpid(), signal.SIGINT)
    return

# Register a signal for cleanup
signal.signal(signal.SIGTERM, handler)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Judicator of Khala system. Handle requests and maintain task data.')
    parser.add_argument("--docker-sock", dest="docker_sock", default=None)
    parser.add_argument("--retry-times", type=int, dest="retry_times", default=None)
    parser.add_argument("--retry-interval", type=int, dest="retry_interval", default=None)

    parser.add_argument("--boot-check-interval", type=int, dest="boot_check_interval", default=None)
    parser.add_argument("--boot-print-log", dest="boot_print_log", action="store_const", const=True, default=False)

    parser.add_argument("--etcd-exe", dest="etcd_exe", default=None)
    parser.add_argument("--etcd-name", dest="etcd_name", default=None)
    parser.add_argument("--etcd-listen-address", dest="etcd_listen_address", default=None)
    parser.add_argument("--etcd-listen-peer-port", type=int, dest="etcd_listen_peer_port", default=None)
    parser.add_argument("--etcd-listen-client-port", type=int, dest="etcd_listen_client_port", default=None)
    parser.add_argument("--etcd-advertise-address", dest="etcd_advertise_address", default=None)
    parser.add_argument("--etcd-advertise-peer-port",  dest="etcd_advertise_peer_port", default=None)
    parser.add_argument("--etcd-advertise-client-port", dest="etcd_advertise_client_port", default=None)
    parser.add_argument("--etcd-cluster-init-discovery", dest="etcd_cluster_init_discovery", default=None)
    parser.add_argument("--etcd-cluster-init-member", dest="etcd_cluster_init_member", default=None)
    parser.add_argument("--etcd-cluster-init-independent", dest="etcd_cluster_init_independent", action="store_const", const=True, default=None)
    parser.add_argument("--etcd-cluster-join-member-client", dest="etcd_cluster_join_member_client", default=None)
    parser.add_argument("--etcd-print-log", dest="etcd_print_log", action="store_const", const=True, default=False)

    parser.add_argument("--mongodb-exe", dest="mongodb_exe", default=None)
    parser.add_argument("--mongodb-name", dest="mongodb_name", default=None)
    parser.add_argument("--mongodb-listen-address", dest="mongodb_listen_address", default=None)
    parser.add_argument("--mongodb-listen-port", type=int, dest="mongodb_listen_port", default=None)
    parser.add_argument("--mongodb-advertise-address", dest="mongodb_advertise_address", default=None)
    parser.add_argument("--mongodb-advertise-port", dest="mongodb_advertise_port", default=None)
    parser.add_argument("--mongodb-replica-set", dest="mongodb_replica_set", default=None)
    parser.add_argument("--mongodb-print-log", dest="mongodb_print_log", action="store_const", const=True, default=False)

    parser.add_argument("--main-name", dest="main_name", default=None)
    parser.add_argument("--main-listen-address", dest="main_listen_address", default=None)
    parser.add_argument("--main-listen-port", type=int, dest="main_listen_port", default=None)
    parser.add_argument("--main-advertise-address", dest="main_advertise_address", default=None)
    parser.add_argument("--main-advertise-port", dest="main_advertise_port", default=None)
    parser.add_argument("--main-print-log", dest="main_print_log", action="store_const", const=True, default=False)

    args = parser.parse_args()

    # Load configuration
    with open("config/templates/boot.json", "r") as f:
        config = json_comment.load(f)
    if args.boot_check_interval is not None:
        config["check_interval"] = args.boot_check_interval
    if args.boot_print_log:
        config.pop("log", None)

    # Generate a logger
    if "log" in config:
        logger = get_logger(
            "boot",
            config["log"]["info"],
            config["log"]["error"]
        )
    else:
        logger = get_logger("boot", None, None)
    logger.info("Judicator boot program started.")

    # If docker-sock is given, generate a docker client for it
    client = docker.APIClient(base_url=args.docker_sock) if args.docker_sock else None

    # Generate services
    services = {}

    # Load and modify config for etcd
    with open("config/templates/etcd.json", "r") as f:
        config_sub = json_comment.load(f)

    if args.retry_times is not None:
        config_sub["daemon"]["retry"]["times"] = args.retry_times
    if args.retry_interval is not None:
        config_sub["daemon"]["retry"]["interval"] = args.retry_interval
    if args.etcd_exe is not None:
        config_sub["etcd"]["exe"] = args.etcd_exe
    if args.etcd_name is not None:
        config_sub["etcd"]["name"] = args.etcd_name
    if args.etcd_listen_address is not None:
        config_sub["etcd"]["listen"]["address"] = transform_address(args.etcd_listen_address, client)
    if args.etcd_listen_peer_port is not None:
        config_sub["etcd"]["listen"]["peer_port"] = str(args.etcd_listen_peer_port)
        config_sub["etcd"]["advertise"]["peer_port"] = str(args.etcd_listen_peer_port)
    if args.etcd_listen_client_port is not None:
        config_sub["etcd"]["listen"]["client_port"] = str(args.etcd_listen_client_port)
        config_sub["etcd"]["advertise"]["client_port"] = str(args.etcd_listen_client_port)
    if args.etcd_advertise_address is not None:
        config_sub["etcd"]["advertise"]["address"] = transform_address(args.etcd_advertise_address, client)
    if args.etcd_advertise_peer_port is not None:
        if args.etcd_advertise_peer_port == "DOCKER":
            config_sub["etcd"]["advertise"]["peer_port"] = str(
                client.port(socket.gethostname(), int(config_sub["etcd"]["listen"]["peer_port"]))[0]["HostPort"]
            )
        else:
            config_sub["etcd"]["advertise"]["peer_port"] = str(args.etcd_advertise_peer_port)
    if args.etcd_advertise_client_port is not None:
        if args.etcd_advertise_client_port == "DOCKER":
            config_sub["etcd"]["advertise"]["client_port"] = str(
                client.port(socket.gethostname(), int(config_sub["etcd"]["listen"]["client_port"]))[0]["HostPort"]
            )
        else:
            config_sub["etcd"]["advertise"]["client_port"] = str(args.etcd_advertise_client_port)
    if args.etcd_cluster_init_discovery is not None:
        config_sub["etcd"]["cluster"] = {"type": "init", "discovery": args.etcd_cluster_init_discovery}
    if args.etcd_cluster_init_member is not None:
        config_sub["etcd"]["cluster"] = {"type": "init", "member": args.etcd_cluster_init_member}
    if args.etcd_cluster_init_independent is not None:
        config_sub["etcd"]["cluster"] = {"type": "init"}
    if args.etcd_cluster_join_member_client is not None:
        config_sub["etcd"]["cluster"] = {"type": "join", "client": args.etcd_cluster_join_member_client}
    if args.etcd_print_log:
        config_sub["daemon"].pop("log_daemon", None)
        config_sub["daemon"].pop("log_etcd", None)
    if args.docker_sock is not None:
        config_sub["etcd"]["exe"] = "etcd"
        if args.etcd_name is None:
            config_sub["etcd"]["name"] = socket.gethostname()

    with open("config/etcd.json", "w") as f:
        f.write(json.dumps(config_sub))
    services["etcd"] = {
        "pid_file": config_sub["daemon"]["pid_file"],
        "command": config_sub["daemon"]["exe"],
        "process": None
    }

    # The same thing for mongodb
    with open("config/templates/mongodb.json", "r") as f:
        config_sub = json_comment.load(f)

    if args.retry_times is not None:
        config_sub["daemon"]["retry"]["times"] = args.retry_times
    if args.retry_interval is not None:
        config_sub["daemon"]["retry"]["interval"] = args.retry_interval
    if args.mongodb_exe is not None:
        config_sub["mongodb"]["exe"] = args.mongodb_exe
    if args.mongodb_name is not None:
        config_sub["mongodb"]["name"] = args.mongodb_name
    if args.mongodb_listen_address is not None:
        config_sub["mongodb"]["listen"]["address"] = transform_address(args.mongodb_listen_address, client)
    if args.mongodb_listen_port is not None:
        config_sub["mongodb"]["listen"]["port"] = str(args.mongodb_listen_port)
        config_sub["mongodb"]["advertise"]["port"] = str(args.mongodb_listen_port)
    if args.mongodb_advertise_address is not None:
        config_sub["mongodb"]["advertise"]["address"] = transform_address(args.mongodb_advertise_address, client)
    if args.mongodb_advertise_port is not None:
        if args.mongodb_advertise_port == "DOCKER":
            config_sub["mongodb"]["advertise"]["port"] = str(
                client.port(socket.gethostname(), int(config_sub["mongodb"]["listen"]["port"]))[0]["HostPort"]
            )
        else:
            config_sub["mongodb"]["advertise"]["port"] = str(args.mongodb_advertise_port)
    if args.mongodb_replica_set is not None:
        config_sub["mongodb"]["replica_set"] = args.mongodb_replica_set
    if args.mongodb_print_log:
        config_sub["daemon"].pop("log_daemon", None)
        config_sub["daemon"].pop("log_mongodb", None)
    if args.docker_sock is not None:
        config_sub["mongodb"]["exe"] = "mongod"
        if args.mongodb_name is None:
            config_sub["mongodb"]["name"] = socket.gethostname()

    with open("config/mongodb.json", "w") as f:
        f.write(json.dumps(config_sub))
    services["mongodb"] = {
        "pid_file": config_sub["daemon"]["pid_file"],
        "command": config_sub["daemon"]["exe"],
        "process": None
    }

    # The same thing for main
    with open("config/templates/main.json", "r") as f:
        config_sub = json_comment.load(f)

    if args.retry_times is not None:
        config_sub["retry"]["times"] = args.retry_times
    if args.retry_interval is not None:
        config_sub["retry"]["interval"] = args.retry_interval
    if args.main_name is not None:
        config_sub["name"] = args.main_name
    if args.main_listen_address is not None:
        config_sub["listen"]["address"] = transform_address(args.main_listen_address, client)
    if args.main_listen_port is not None:
        config_sub["listen"]["port"] = str(args.main_listen_port)
        config_sub["advertise"]["port"] = str(args.main_listen_port)
    if args.main_advertise_address is not None:
        config_sub["advertise"]["address"] = transform_address(args.main_advertise_address, client)
    if args.main_advertise_port is not None:
        if args.main_advertise_port == "DOCKER":
            config_sub["advertise"]["port"] = str(
                client.port(socket.gethostname(), int(config_sub["listen"]["port"]))[0]["HostPort"]
            )
        else:
            config_sub["advertise"]["port"] = str(args.main_advertise_port)
    if args.main_print_log:
        config_sub.pop("log", None)
    if args.docker_sock is not None:
        if args.main_name is None:
            config_sub["name"] = socket.gethostname()
        client = docker.APIClient(base_url=args.docker_sock)

    with open("config/main.json", "w") as f:
        f.write(json.dumps(config_sub))
    services["main"] = {
        "pid_file": config_sub["pid_file"],
        "command": config_sub["exe"],
        "process": None
    }

    # Generate pid files for service daemons
    for s in services:
        with open(services[s]["pid_file"], "w") as f:
            f.write("-1")

    # Generate start and exit order list
    start_order = ["etcd", "mongodb", "main"]
    exit_order = start_order[: : -1]

    # Check whether service daemons are running regularly
    while True:
        try:
            for s in start_order:
                logger.info("Checking status of service %s." % s)
                # Try to open the pid file of the service
                try:
                    with open(services[s]["pid_file"], "r+") as f:
                        # If opened successfully (this should always happen), try to get a lock
                        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        logger.debug("Pid file %s locked successfully." % services[s]["pid_file"])

                        # If the lock is obtained, do the regular check up for the service and start it, if required
                        try:
                            # If the process is None or the process has exited, restart it and rewrite the pid file
                            if (not services[s]["process"]) or services[s]["process"].poll() is not None:
                                logger.warning("Service %s is down. Trying to start the service and write pid file." % s)
                                services[s]["process"] = subprocess.Popen(services[s]["command"])
                                f.truncate()
                                f.write(str(services[s]["process"].pid))
                            else:
                                logger.info("Service %s is running." % s)
                        except:
                            logger.error("Exception occurs when checking service %s." % s, exc_info=True)
                        finally:
                            # The lock must be released
                            fcntl.lockf(f, fcntl.LOCK_UN)
                            logger.debug("Pid file %s unlocked successfully." % services[s]["pid_file"])
                except OSError as e:
                    if e.errno == errno.EACCES or e.errno == errno.EAGAIN:
                        # If OSError occur and errno equals EACCES or EAGAIN, this means the lock can not be obtained
                        # Then, do nothing
                        # This could happen when the service is being maintained
                        logger.warning("Failed to obtain lock for %s, skip corresponding service check." % s)
                    else:
                        raise e
                except:
                    logger.error("Fatal exception occurs when checking service %s." % s, exc_info=True)
            time.sleep(config["check_interval"])

        except KeyboardInterrupt:
            logger.info("Receiving SIGINT. Quiting the whole program.")
            break

    # Clean all services
    for s in exit_order:
        if services[s]["process"]:
            os.kill(services[s]["process"].pid, signal.SIGINT)
            logger.info("Killing service %s." % s)
            services[s]["process"].wait()
            logger.info("Service %s finished." % s)

    logger.info("Exiting.")
