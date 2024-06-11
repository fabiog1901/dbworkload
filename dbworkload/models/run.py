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
    "max(ms)",
]


def signal_handler(sig, frame):
    """Handles Ctrl+C events gracefully,
    ensuring all running processes are closed rather than killed.

    Args:
        sig (_type_):
        frame (_type_):
    """
    logger.info("KeyboardInterrupt signal detected. Stopping processes...")

    # send the poison pill to each worker.
    # if dbworkload cannot graceful shutdown due
    # to processes being still in the init phase
    # when the pill is sent, a subsequent Ctrl+C will cause
    # the pill to overflow the kill_q
    # and raise the queue.Full exception, forcing to quit.
    for _ in range(concurrency):
        try:
            kill_q.put(None, timeout=0.1)
        except queue.Full:
            logger.error("Timed out")
            sys.exit(1)

    logger.debug("Sent poison pill to all threads")


def ramp_up(processes: list, ramp_interval: int):
    for p in processes:
        logger.debug("Starting a new Process...")
        p.start()
        time.sleep(ramp_interval)


def run(
    conc: int,
    workload_path: str,
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
    def gracefully_shutdown(s):
        # wait for final stats reports to come in,
        # then print final stats and quit
        while s < concurrency:
            msg = q.get(block=True, timeout=2.0)
            if isinstance(msg, list):
                stats.add_tds(msg)
            else:
                logger.error("Timed out, quitting")
                sys.exit(1)
            s += 1

        print_stats(stats)
        sys.exit(0)

    logger.setLevel(log_level)

    global concurrency
    concurrency = conc
    
    global kill_q
    global q

    workload = dbworkload.utils.common.import_class_at_runtime(workload_path)

    # register Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)

    disable_stats = False

    if frequency == 0:
        disable_stats = True
        frequency = 10

    stats = dbworkload.utils.common.Stats(frequency, prom_port)

    if iterations:
        iterations = iterations // concurrency

    q = mp.Queue(maxsize=0)
    kill_q = mp.Queue(maxsize=concurrency)

    c = 0
    s = 0

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


    while True:
        try:
            # read from the queue for stats or completion messages
            msg = q.get(block=False)
            # a stats report is a list obj
            if isinstance(msg, list):
                stats.add_tds(msg)
                s += 1
            else:
                # if it's not a stat message, then the worker returned
                c += 1
        except queue.Empty:
            pass

        # once the sum of the completion messages matches 
        # the count of threads, identify what type of 
        # completion message it was
        if c >= concurrency:
            if msg == "task_done":
                logger.info(
                    "Requested iteration/duration limit reached. Printing final stats"
                )
                gracefully_shutdown(s)
            elif msg == "poison_pill":
                logger.info("Printing final stats")
                gracefully_shutdown(s)
            elif isinstance(msg, Exception):
                logger.error(f"error_type={msg.__class__.__name__}, msg={msg}")
                sys.exit(1)
            else:
                logger.error(f"unrecognized message: {msg}")
                sys.exit(1)

        if s >= concurrency:
            print_stats(stats)
            stats.new_window()
            s = 0


def worker(
    thread_count: int,
    q: mp.Queue,
    kill_q: mp.Queue,
    log_level: str,
    conn_info: ConnInfo,
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
        log_level (str): log level to set the logger to
        conn_info (ConnInfo): connection data
        workload (object): workload class object
        args (dict): args to init the workload class
        iterations (int): count of workload iteration before returning
        duration (int): seconds before returning
        conn_duration (int): seconds before restarting the database connection
        disable_stats: (bool): flag to send or not stats back to the mainthread
        conc: (int): the total number of threads
        id_base_counter (int): the base counter to generate ID for each Process
        id (int): the ID of the thread
        driver (str): the friendly driver name
    """

    def gracefully_return(msg):
        # send notification to MainThread
        q.put(msg)
        # send final stats
        q.put(ws.get_tdigests(), block=False)

        # wait for all Processes children threads to return before
        # letting the Process MainThread return
        if threading.current_thread().name == "MainThread":
            for x in threads:
                x.join()

    logger.setLevel(log_level)

    logger.debug(f"My ID is {id}")

    threads: list[threading.Thread] = []

    if threading.current_thread().name == "MainThread":
        
        # capture KeyboardInterrupt and do nothing
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        
        # only the MainThread of a child Process spawns Threads    
        for i in range(thread_count):
            thread = threading.Thread(
                target=worker,
                daemon=True,
                args=(
                    0,
                    q,
                    kill_q,
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

    ws = dbworkload.utils.common.WorkerStats()

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
            return gracefully_return("poison_pill")
        except queue.Empty:
            pass

        stat_time = time.time() + 10
        try:
            logger.debug(f"driver: {driver}, params: {conn_info.params}")
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

                while True:
                    # listen for termination messages (poison pill)
                    try:
                        kill_q.get(block=False)
                        logger.debug("Poison pill received")
                        return gracefully_return("poison_pill")
                    except queue.Empty:
                        pass

                    # return if the limits of either iteration count and duration have been reached
                    if (iterations and c >= iterations) or (
                        duration and time.time() >= endtime
                    ):
                        logger.debug("Task completed!")
                        return gracefully_return("task_done")

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
                            ws.add_latency_measurement("__retries__", 0)

                        # if retries matches max_retries, then it's a total failure and we don't record the txn time
                        if not disable_stats and retries < MAX_RETRIES:
                            ws.add_latency_measurement(
                                txn.__name__, time.time() - start
                            )

                    c += 1
                    if not disable_stats:
                        ws.add_latency_measurement(
                            "__cycle__", time.time() - cycle_start
                        )

                    if q.full():
                        logger.error("=========== Q FULL!!!! ======================")
                    if time.time() >= stat_time:
                        q.put(ws.get_tdigests(), block=False)
                        ws.new_window()
                        stat_time = time.time() + 10  # frequency

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
                if str(e).startswith("ORA-00942: table or view does not exist"):
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


def print_stats(stats: dbworkload.utils.common.Stats):
    print(tabulate.tabulate(stats.calculate_stats(), HEADERS, intfmt=",", floatfmt=",.2f"), "\n")


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
