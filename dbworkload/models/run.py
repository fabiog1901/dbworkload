#!/usr/bin/python

import dbworkload.utils.common
from dbworkload.cli.dep import ConnInfo
import logging
import logging.handlers
import multiprocessing as mp
import queue
import random
import signal
import sys
import tabulate
import threading
import time
import traceback
import sys

# drivers
# import psycopg
# import mysql.connector
# import mysql.connector.errorcode
# import mysql.connector.errors
# import mariadb
# import oracledb

# import pyodbc

# import pymongo
# from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT, Session
# from cassandra.policies import (
#     WhiteListRoundRobinPolicy,
#     DowngradingConsistencyRetryPolicy,
# )
# from cassandra.query import tuple_factory
# from cassandra.policies import ConsistencyLevel


DEFAULT_SLEEP = 3
MAX_RETRIES = 3

logger = logging.getLogger("dbworkload")


HEADERS: list = [
    "id",
    "elapsed",
    "tot_ops",
    "tot_ops/s",
    "period_ops",
    "period_ops/s",
    "mean(ms)",
    "p50(ms)",
    "p90(ms)",
    "p95(ms)",
    "p99(ms)",
    "pMax(ms)",
]


def signal_handler(sig, frame):
    """Handles Ctrl+C events gracefully,
    ensuring all running processes are closed rather than killed.

    Args:
        sig (_type_):
        frame (_type_):
    """
    global stats
    global concurrency
    logger.info("KeyboardInterrupt signal detected. Stopping processes...")

    # send the poison pill to each worker
    for _ in range(concurrency):
        kill_q.put(None)

    # wait until all workers return
    start = time.time()
    c = 0
    timeout = True
    while c < concurrency and timeout:
        try:
            kill_q2.get(block=False)
            c += 1
        except:
            pass

        time.sleep(0.01)
        timeout = time.time() < start + 5

    if not timeout:
        logger.info("Timeout reached - forcing processes to stop")

    logger.info("Printing final stats")
    # empty the queue before printing final stats
    while True:
        try:
            msg = q.get(block=False)
            if isinstance(msg, tuple):
                stats.add_latency_measurement(*msg)
        except queue.Empty:
            __print_stats()
            break

    sys.exit(0)


def ramp_up(processes: list, ramp_interval: int):
    for p in processes:
        logger.debug("Starting a new Process...")
        p.start()
        time.sleep(ramp_interval)


def run(
    conc: int,
    workload_path: str,
    builtin_workload: str,
    frequency: int,
    prom_port: int,
    iterations: int,
    procs: int,
    ramp: int,
    conn_info: dict,
    duration: int,
    conn_duration: int,
    args: dict,
    driver: str,
    log_level: str,
):
    logger.setLevel(log_level)

    global stats
    global concurrency
    global kill_q
    global kill_q2
    global q

    concurrency = conc

    workload = dbworkload.utils.common.import_class_at_runtime(
        workload_path if workload_path else builtin_workload
    )

    signal.signal(signal.SIGINT, signal_handler)

    disable_stats = False

    if frequency == 0:
        disable_stats = True
        frequency = 10

    stats = dbworkload.utils.common.Stats(frequency, prom_port)

    if iterations:
        iterations = iterations // concurrency

    q = mp.Queue(maxsize=0)
    kill_q = mp.Queue()
    kill_q2 = mp.Queue()

    c = 0

    threads_per_proc = dbworkload.utils.common.get_threads_per_proc(procs, conc)
    ramp_interval = int(ramp / len(threads_per_proc))

    # each Process must generate an ID for each of its threads,
    # starting from the id_base_counter and incrementing by 1.
    # for each Process' MainThread, the id_base_counter is also its id.
    id_base_counter = 0

    processes: list[mp.Process] = []
    for x in threads_per_proc:
        processes.append(
            mp.Process(
                target=worker,
                args=(
                    x - 1,
                    q,
                    kill_q,
                    kill_q2,
                    log_level,
                    conn_info,
                    workload,
                    args,
                    iterations,
                    duration,
                    conn_duration,
                    disable_stats,
                    conc,
                    id_base_counter,
                    id_base_counter,
                    driver,
                ),
            )
        )
        id_base_counter += x

    threading.Thread(
        target=ramp_up, daemon=True, args=(processes, ramp_interval)
    ).start()

    try:
        stat_time = time.time() + frequency
        while True:
            try:
                # read from the queue for stats or completion messages
                msg = q.get(block=False)
                if isinstance(msg, tuple):
                    stats.add_latency_measurement(*msg)
                else:
                    # if it's not a stat message, then the worker returned
                    c += 1
            except queue.Empty:
                pass

            if c >= concurrency:
                if isinstance(msg, Exception):
                    logger.error(f"error_type={msg.__class__.__name__}, msg={msg}")
                    sys.exit(1)
                elif msg is None:
                    logger.info(
                        "Requested iteration/duration limit reached. Printing final stats"
                    )

                    # empty the queue before printing final stats
                    while True:
                        try:
                            msg = q.get(block=False)
                            if isinstance(msg, tuple):
                                stats.add_latency_measurement(*msg)
                        except queue.Empty:
                            __print_stats()
                            break

                    sys.exit(0)

                else:
                    logger.error(f"unrecognized message: {msg}")
                    sys.exit(1)

            if time.time() >= stat_time:
                __print_stats()
                stats.new_window()
                stat_time = time.time() + frequency

    except Exception as e:
        logger.error(traceback.format_exc())


def worker(
    thread_count: int,
    q: mp.Queue,
    kill_q: mp.Queue,
    kill_q2: mp.Queue,
    log_level: str,
    conn_info: dict,
    workload: object,
    args: dict,
    iterations: int,
    duration: int,
    conn_duration: int,
    disable_stats: bool,
    conc: int,
    id_base_counter: int = 0,
    id: int = 0,
    driver: str = None,
):
    """Process worker function to run the workload in a multiprocessing env

    Args:
        thread_count (int): The number of threads to create
        q (mp.Queue): queue to report query metrics
        kill_q (mp.Queue): queue to handle stopping the worker
        kill_q2 (mp.Queue): queue to handle stopping the worker
        dburl (str): connection string to the database
        workload (object): workload class object
        args (dict): args to init the workload class
        iterations (int): count of workload iteration before returning
        duration (int): seconds before returning
        conn_duration (int): seconds before restarting the database connection
        disable_stats: (bool): flag to send or not stats back to the mainthread
        conc: (int): the total number of threads
        id_base_counter (int): the base counter to generate ID for each Process
        id (int): the ID of the thread
    """
    logger.setLevel(log_level)

    logger.debug(f"My ID is {id}")

    threads: list[threading.Thread] = []
    for i in range(thread_count):
        thread = threading.Thread(
            target=worker,
            daemon=True,
            args=(
                0,
                q,
                kill_q,
                kill_q2,
                log_level,
                conn_info,
                workload,
                args,
                iterations,
                duration,
                conn_duration,
                disable_stats,
                conc,
                None,
                id_base_counter + i + 1,
                driver,
            ),
        )
        thread.start()
        threads.append(thread)

    if threading.current_thread().name == "MainThread":
        # capture KeyboardInterrupt and do nothing
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    # catch exception while instantiating the workload class
    try:
        w = workload(args)
    except Exception as e:
        stack_lines = traceback.format_exc()
        q.put(Exception(stack_lines))
        return

    c = 0
    endtime = 0
    conn_endtime = 0

    if duration:
        endtime = time.time() + duration

    run_init = True

    while True:
        if conn_duration:
            # reconnect every conn_duration +/- 20%
            conn_endtime = time.time() + int(conn_duration * random.uniform(0.8, 1.2))
        # listen for termination messages (poison pill)
        try:
            kill_q.get(block=False)
            logger.debug("Poison pill received")
            kill_q2.put(None)
            for x in threads:
                x.join()

            return
        except queue.Empty:
            pass

        try:
            logger.debug(f"driver: {driver}, conn_info: {conn_info}")
            # with Cluster().connect('bank') as conn:
            with get_connection(driver, conn_info) as conn:
                logger.debug("Connection started")

                # execute setup() only once per thread
                if run_init:
                    run_init = False

                    if hasattr(w, "setup") and callable(w.setup):
                        logger.debug("Executing setup() function")
                        run_transaction(
                            conn,
                            lambda conn: w.setup(conn, id, conc),
                            driver,
                            max_retries=MAX_RETRIES,
                        )
                    else:
                        logger.debug("No setup() function found.")

                while True:
                    # listen for termination messages (poison pill)
                    try:
                        kill_q.get(block=False)
                        logger.debug("Poison pill received")
                        kill_q2.put(None)
                        for x in threads:
                            x.join()
                        return
                    except queue.Empty:
                        pass

                    # return if the limits of either iteration count and duration have been reached
                    if (iterations and c >= iterations) or (
                        duration and time.time() >= endtime
                    ):
                        logger.debug("Task completed!")

                        # send task completed notification (a None)
                        q.put(None)
                        for x in threads:
                            x.join()
                        return

                    # break from the inner loop if limit for connection duration has been reached
                    # this will cause for the outer loop to reset the timer and restart with a new conn
                    if conn_duration and time.time() >= conn_endtime:
                        logger.debug(
                            "conn_duration reached, will reset the connection."
                        )
                        break

                    cycle_start = time.time()
                    for txn in w.loop():
                        start = time.time()
                        retries = run_transaction(
                            conn,
                            lambda conn: txn(conn),
                            driver,
                            max_retries=MAX_RETRIES,
                        )

                        # record how many retries there were, if any
                        for _ in range(retries):
                            q.put(("__retries__", 0))

                        if q.full():
                            logger.warning(
                                "==============  THE QUEUE IS FULL - STATS ARE NOT RELIABLE!!  ================"
                            )
                        # if retries matches max_retries, then it's a total failure and we don't record the txn time
                        if not q.full() and not disable_stats and retries < MAX_RETRIES:
                            q.put((txn.__name__, time.time() - start))

                    c += 1
                    if not q.full() and not disable_stats:
                        q.put(("__cycle__", time.time() - cycle_start))

        except Exception as e:
            if driver == "psycopg":
                import psycopg
                if isinstance(e, psycopg.errors.UndefinedTable):
                    q.put(e)
                    return
                log_and_sleep(e)

            elif driver == "mysql":
                import mysql.connector.errorcode
                if e.errno == mysql.connector.errorcode.ER_NO_SUCH_TABLE:
                    q.put(e)
                    return
                log_and_sleep(e)
                
            elif driver == "maria":
                if str(e).endswith(" doesn't exist"):
                    q.put(e)
                    return
                log_and_sleep(e)
            
            elif driver == "oracle":
                if e == ("ORA-00942: table or view does not exist"):
                    q.put(e)
                    return
                log_and_sleep(e)
                

            else:
                # for all other Exceptions, report and return
                logger.error(type(e), stack_info=True)
                q.put(e)
                return


def log_and_sleep(e: Exception):
    logger.error(f"error_type={e.__class__.__name__}, msg={e}")
    logger.info("Sleeping for %s seconds" % (DEFAULT_SLEEP))
    time.sleep(DEFAULT_SLEEP)


def __print_stats():
    print(tabulate.tabulate(stats.calculate_stats(), HEADERS), "\n")


def run_transaction(conn, op, driver: str, max_retries=3):
    """
    Execute the operation *op(conn)* retrying serialization failure.

    If the database returns an error asking to retry the transaction, retry it
    *max_retries* times before giving up (and propagate it).
    """
    for retry in range(1, max_retries + 1):
        try:
            op(conn)
            # If we reach this point, we were able to commit, so we break
            # from the retry loop.
            return retry - 1
        except Exception as e:
            if driver == "psycopg":
                import psycopg.errors
                if isinstance(e, psycopg.errors.SerializationFailure):
                    # This is a retry error, so we roll back the current
                    # transaction and sleep for a bit before retrying. The
                    # sleep time increases for each failed transaction.
                    logger.debug(f"SerializationFailure:: {e}")
                    conn.rollback()
                    time.sleep((2**retry) * 0.1 * (random.random() + 0.5))
            else:
                raise e

    logger.debug(f"Transaction did not succeed after {max_retries} retries")
    return retry


def get_connection(driver: str, conn_info: ConnInfo):
    if driver == "postgres":
        import psycopg
        return psycopg.connect(**conn_info.params)
    elif driver == "mysql":
        import mysql.connector        
        return mysql.connector.connect(**conn_info.params)
    elif driver == "maria":
        import mariadb
        return mariadb.connect(**conn_info.params)
    elif driver == "oracle":
        import oracledb
        conn = oracledb.connect(**conn_info.params)
        conn.autocommit = conn_info.extras.get("autocommit", False)
        return conn
    # elif driver == "sqlserver":
    #     return
    elif driver == "mongo":
        import pymongo
        return pymongo.MongoClient(**conn_info)
    # elif driver == "cassandra":
    #     profile = ExecutionProfile(
    #         load_balancing_policy=WhiteListRoundRobinPolicy(["127.0.0.1"]),
    #         retry_policy=DowngradingConsistencyRetryPolicy(),
    #         consistency_level=ConsistencyLevel.LOCAL_QUORUM,
    #         serial_consistency_level=ConsistencyLevel.LOCAL_SERIAL,
    #         request_timeout=15,
    #         row_factory=tuple_factory,
    #     )
    #     cluster = Cluster(execution_profiles={EXEC_PROFILE_DEFAULT: profile})
    #     # session = cluster.connect()
    #     return cluster.connect()

