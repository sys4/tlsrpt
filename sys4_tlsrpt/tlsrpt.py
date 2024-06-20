#
#    Copyright (C) 2024 sys4 AG
#    Author Boris Lohner bl@sys4.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#

import datetime
import json
import logging
import os
import random
from abc import ABCMeta, abstractmethod
from pathlib import Path
import socket
import subprocess
import sys
import sqlite3
import time

# Constants
TLSRPT_FETCHER_VERSION_STRING_V1 = "TLSRPT FETCHER v1 domain list"
TLSRPT_TIMEFORMAT = "%Y-%m-%d %H:%M:%S"
TLSRPT_MAX_READ_FETCHER = 16000000
TLSRPT_MAX_READ_RECEIVER = 16000000
# Exit codes
EXIT_DB_SETUP_FAILURE = 1
EXIT_WRONG_DB_VERSION = 2
# Development mode
DEVELMODE = True


class ConfigReceiver:
    @property
    def receiver_dbname(self):
        return "/tmp/tlsrpt-receiver.sqlite"

    @property
    def receiver_socketname(self):
        return "/tmp/tlsrpt-receiver.socket"

    @property
    def receiver_sockettimeout(self):
        """Database will commit every n seconds """
        return 5

    @property
    def max_uncommited_datagrams(self):
        """Database will commit after n datagrams """
        return 1000

    @property
    def receiver_logfilename(self):
        return "/tmp/tlsrpt-receiver.log"

    @property
    def fetcher_logfilename(self):
        return self.receiver_logfilename

    @property
    def dump_path_for_invalid_datagram(self):
        return "/tmp/debug-payload"

    @property
    def hook_pre_fetchdomainlist(self):
        return None


class ConfigReporter:

    @property
    def reporter_logfilename(self):
        return "/tmp/tlsrpt-reporter.log"

    @property
    def reporter_dbname(self):
        return "/tmp/tlsrpt-reporter.sqlite"

    @property
    def reporter_fetchers(self):
        return ["python3 tlsrpt-fetcher.py "]

    @property
    def organization_name(self):
        return "EXAMPLE.inc"

    @property
    def contact_info(self):
        return "sender@example.com"

    @property
    def max_receiver_timeout(self):
        return 1

    @property
    def max_receiver_timediff(self):
        return -2

    @property
    def max_retries_domainlist(self):
        return 3

    @property
    def min_wait_domainlist(self):
        return 300

    @property
    def max_wait_domainlist(self):
        return 360

    def next_time_domainlist(self):
        """
        Calculates a random wait period

        :return: seconds to wait before next retry
        """
        waits = random.randint(self.min_wait_domainlist, self.max_wait_domainlist)  # 5 to 6 minutes
        if DEVELMODE:
            random.randint(1, 3)  # 1 to 3 seconds for testing
        return tlsrpt_utc_time_now() + datetime.timedelta(seconds=waits)


class TLSRPTReceiver(metaclass=ABCMeta):
    @abstractmethod
    def add_datagram(self, datagram):
        pass

    @abstractmethod
    def socket_timeout(self):
        pass


class DummyReceiver(TLSRPTReceiver):
    def __init__(self, dolog):
        self.dolog = dolog

    def add_datagram(self, datagram):
        if self.dolog:
            logging.info("Dummy receiver got datagram of {len(datagram)} bytes")

    def socket_timeout(self):
        if self.dolog:
            logging.info("Dummy receiver got socket timeout")


class TLSRPTReceiverSQLite(TLSRPTReceiver):
    cfg: ConfigReceiver

    def __init__(self, config):
        self.cfg = config
        self.uncommitted_datagrams = 0
        self.dbname = self.cfg.receiver_dbname
        self.con = sqlite3.connect(self.dbname)
        self.cur = self.con.cursor()
        if self._check_database():
            logging.info("Database %s looks OK", self.dbname)
        else:
            logging.info("Create new database %s", self.dbname)
            self._setup_database()
        # Settings for flushing to disk
        self.commitEveryN = self.cfg.max_uncommited_datagrams

    def _setup_database(self):
        try:
            ddl = ["CREATE TABLE finalresults(day, domain, policy, cntrtotal, cntrfailure, "
                   "PRIMARY KEY(day, domain, policy))",
                   "CREATE TABLE failures(day, domain, policy, reason, cntr, "
                   "PRIMARY KEY(day, domain, policy, reason))",
                   "CREATE TABLE tlsrptreceiverdbversion(version, installdate)",
                   "INSERT INTO tlsrptreceiverdbversion(version, installdate) "
                   " VALUES(1,strftime('%Y-%m-%d %H-%M-%f','now'))"]

            for ddlstatement in ddl:
                self.cur.execute(ddlstatement)
            self.con.commit()
            logging.info("Database '%s' setup finished", self.dbname)
        except Exception as err:
            logging.error("Database '%s' setup failed: %s", self.dbname, err)
            sys.exit(EXIT_DB_SETUP_FAILURE)

    def _check_database(self):
        try:
            self.cur.execute("SELECT version, installdate FROM tlsrptreceiverdbversion")
            row = self.cur.fetchone()
            if row[0] != 1:
                logging.error("Database has wrong version, expected 1 but got %s", row)
                sys.exit(EXIT_WRONG_DB_VERSION)
            return True
        except Exception as err:
            logging.error("Database check failed: %s", err)
            return False

    def timed_commit(self):
        logging.debug("Database commit due to timeout with %d datagrams" % self.uncommitted_datagrams)
        self.uncommitted_datagrams = 0
        self.con.commit()

    def commit_after_n_datagrams(self):
        logging.debug("Database commit with %d datagrams" % self.uncommitted_datagrams)
        self.uncommitted_datagrams = 0
        self.con.commit()

    def _add_policy(self, day, domain, policy):
        # Romove unneeded keys from policy before writing to database, keeping needed values
        policy_failed = policy.pop("f")
        failures = policy.pop("failure-details", [])
        policy.pop("t", None)
        p = str(policy)
        self.cur.execute(
            "INSERT INTO finalresults (day, domain, policy, cntrtotal, cntrfailure) VALUES(?,?,?,1,?) "
            "ON CONFLICT(day, domain, policy) "
            "DO UPDATE SET cntrtotal=cntrtotal+1, cntrfailure=cntrfailure+?",
            (day, domain, p, policy_failed, policy_failed))

        for f in failures:
            self.cur.execute(
                "INSERT INTO failures (day, domain, policy, reason, cntr) VALUES(?,?,?,?,1) "
                "ON CONFLICT(day, domain, policy, reason) "
                "DO UPDATE SET cntr=cntr+1",
                (day, domain, p, str(f)))

    def _add_policies_from_datagram(self, day, datagram):
        if "policies" not in datagram:
            logging.warning("No policies found in datagram: %s", datagram)
            return
        for policy in datagram["policies"]:
            self._add_policy(day, datagram["d"], policy)

    def add_datagram(self, datagram):
        self._add_policies_from_datagram(tlsrpt_utc_date_now(), datagram)

        self.uncommitted_datagrams += 1
        if self.uncommitted_datagrams >= self.commitEveryN:
            self.commit_after_n_datagrams()

    def socket_timeout(self):
        self.timed_commit()


class TLSRPTFetcherSQLite(TLSRPTReceiverSQLite):
    def fetch_domain_list(self, day):
        logging.info(f"TLSRPT fetcher domain list starting for day {day}")
        # Protocol header
        print(TLSRPT_FETCHER_VERSION_STRING_V1)
        # send timeout in seconds so fetching can be rescheduled after a timeout commit, or warn about too big delay
        print(self.cfg.receiver_sockettimeout)
        # send time so fetching can be rescheduled to account for clock offset, or warn about too big delay
        print(tlsrpt_utc_time_now().strftime(TLSRPT_TIMEFORMAT))
        # could use member cur because this will be called from fetcher which is supposed to be completely
        # separate from receiver, but let´s keep this cursor local to this method
        dlcursor = self.con.cursor()
        dlcursor.execute("SELECT DISTINCT domain FROM finalresults WHERE day=?", (day,))
        linenumber = 0
        for row in dlcursor:
            try:
                linenumber += 1
                print(row[0])
            except BrokenPipeError as err:
                logging.warning(f"Error when writing line {linenumber} : ", err)
        print(".")

    def fetch_domain_details(self, day, domain):
        logging.info(f"TLSRPT fetcher domain details starting for day {day} and domain {domain}")
        policies = {}
        dlcursor = self.con.cursor()
        dlcursor.execute("SELECT domain, policy, cntrtotal, cntrfailure FROM finalresults WHERE day=? AND domain=?",
                         (day, domain))
        for row in dlcursor:
            (domain, policy, cntrtotal, cntrfailure) = row
            if policy not in policies:  # need to create new dict entry
                policies[policy] = {"cntrtotal": 0, "cntrfailure": 0, "failures": {}}
            policies[policy]["cntrtotal"] += cntrtotal
            policies[policy]["cntrfailure"] += cntrfailure

        dlcursor.execute("SELECT policy, reason, cntr FROM failures WHERE day=? AND domain=?", (day, domain))
        for row in dlcursor:
            (policy, reason, cntr) = row
            if reason not in policies[policy]["failures"]:  # need to create new dict entry
                policies[policy]["failures"][reason] = 0
            policies[policy]["failures"][reason] += cntr
        details = {"d": domain, "policies": policies}
        print(json.dumps(details, indent=4))


class TLSRPTReporter:
    # REVIEW: It is not necesarry to declare instance attributes here.
    # In fact, by declaring cfg here, we would declare it as class attribute
    # that is shared by all instances of TLSRPTReporter. Setting the
    # instance attribute in the __init__ function is all that is needed.
    # cfg: ConfigReporter

    def __init__(self, config: ConfigReporter):
        """
        :type config: ConfigReporter
        """
        self.cfg = config
        self.dbname = self.cfg.reporter_dbname
        self.con = sqlite3.connect(self.dbname)
        self.cur = self.con.cursor()
        self.curtoupdate = self.con.cursor()
        self.wakeuptime = tlsrpt_utc_time_now()
        if self._check_database():
            logging.info("Database %s looks OK", self.dbname)
        else:
            logging.info("Create new database %s", self.dbname)
            self._setup_database()

    def _setup_database(self) -> None:
        """
        Create the database table structure. If the database setup cannot be
        completed, program execution is terminated with non-zero return value.
        """
        try:
            ddl = ["CREATE TABLE fetchjobs(day, fetcherindex, fetcher, retries, status, nexttry, "
                   "PRIMARY KEY(day, fetcherindex))",
                   "CREATE TABLE reports(day, domain, report, PRIMARY KEY(day, domain))",
                   "CREATE TABLE reportdata(day, domain, data, fetcherindex, fetcher, retries, status, nexttry, "
                   "PRIMARY KEY(day, domain, fetcherindex))",
                   "CREATE TABLE destinations(day, domain, destination, retries, status, nexttry, "
                   "PRIMARY KEY(day, domain, destination))",
                   "CREATE TABLE tlsrptreporterdbversion(version, installdate)",
                   "INSERT INTO tlsrptreporterdbversion(version, installdate) "
                   " VALUES(1,strftime('%Y-%m-%d %H-%M-%f','now'))"]
            for ddlstatement in ddl:
                logging.debug("Database '%s' DDL %s", self.dbname, ddlstatement)
                self.cur.execute(ddlstatement)
            self.con.commit()
            logging.info("Database '%s' setup finished", self.dbname)
        except Exception as err:
            logging.error("Database '%s' setup failed: %s", self.dbname, err)
            sys.exit(EXIT_DB_SETUP_FAILURE)

    def _check_database(self) -> bool:
        """
        Tries to run a database query, returns True if database has the correct
        version and works as expected. If the database has wrong database
        version, the whole program execution is terminated.
        """
        try:
            self.cur.execute("SELECT version, installdate FROM tlsrptreporterdbversion")
            row = self.cur.fetchone()
            print("DB CHECK ROW IS ", row)
            if row[0] != 1:
                logging.error("Database has wrong version, expected 1 but got %s", row)
                sys.exit(EXIT_WRONG_DB_VERSION)
            return True
        except Exception as err:
            logging.error("Database check failed: %s", err)
            return False

    def check_day(self):
        logging.debug("Check day")
        cur = self.con.cursor()
        yesterday = tlsrpt_utc_date_yesterday()
        if DEVELMODE:  # use todays data during development
            yesterday = tlsrpt_utc_date_now()
        now = tlsrpt_utc_time_now()
        cur.execute("SELECT * FROM fetchjobs WHERE day=?", (yesterday,))
        row = cur.fetchone()
        if row is not None:  # Jobs already exist
            self.wake_up_at(tlsrpt_utc_time_now() + datetime.timedelta(hours=0, seconds=20))  # TODO
            return
        # create now fetcher jobs
        fidx = 0
        for fetcher in self.cfg.reporter_fetchers:
            fidx += 1
            cur.execute("INSERT INTO fetchjobs (day, fetcherindex, fetcher, retries, status, nexttry)"
                        "VALUES (?,?,?,0,NULL,?)", (yesterday, fidx, fetcher, now))
        self.wake_up_at(tlsrpt_utc_date_now() + datetime.timedelta(hours=24, seconds=20))
        self.con.commit()

    def collect_domains(self):
        logging.debug("Collect domains")
        curs = self.con.cursor()
        curu = self.con.cursor()
        now = tlsrpt_utc_time_now()
        curs.execute("SELECT day, fetcherindex, fetcher, retries FROM fetchjobs "
                     "WHERE status IS NULL AND nexttry<?", (now,))
        for row in curs:
            (day, fetcherindex, fetcher, retries) = row
            if self.collect_domains_from(day, fetcher, fetcherindex):
                curu.execute("UPDATE fetchjobs SET status='ok' WHERE day=? AND fetcherindex=?", (day, fetcherindex))
            elif retries < self.cfg.max_retries_domainlist:
                curu.execute("UPDATE fetchjobs SET retries=retries+1, nexttry=? WHERE day=? AND fetcherindex=?",
                             (self.cfg.next_time_domainlist(), day, fetcherindex))
            else:
                curu.execute("UPDATE fetchjobs SET status='timedout' WHERE day=? AND fetcherindex=?",
                             (day, fetcherindex))
        self.con.commit()

    def collect_domains_from(self, day, fetcher, fetcherindex):
        """
        Fetch the list of domains from one of the fetchers

        :param day:
        :type fetcher: str
        :type fetcherindex: int
        """
        logging.debug("Collect domains from %d %s", fetcherindex, fetcher)
        args = fetcher.split()
        args.append(day.__str__())
        fetcherpipe = subprocess.Popen(args, stdout=subprocess.PIPE)
        versionheader = fetcherpipe.stdout.readline().decode('utf-8').rstrip()
        logging.debug(f"From fetcher {fetcherindex} got version header: {versionheader}")
        if versionheader != TLSRPT_FETCHER_VERSION_STRING_V1:
            logging.error(f"Unsupported protocol version from fetcher {fetcherindex} '{fetcher}': {versionheader}")
            return False
        # get socket timeout and therefore the commit lag of this receiver
        receiver_timeout = fetcherpipe.stdout.readline().decode('utf-8').rstrip()
        if int(receiver_timeout) > self.cfg.max_receiver_timeout:
            logging.warning(f"Receiver timeout {receiver_timeout} greater than maximum of "
                            f"{self.cfg.max_receiver_timeout} on fetcher {fetcherindex} {fetcher}")
        # get current time of this receiver
        receiver_time_string = fetcherpipe.stdout.readline().decode('utf-8').rstrip()
        receiver_time = datetime.datetime.strptime(receiver_time_string, TLSRPT_TIMEFORMAT). \
            replace(tzinfo=datetime.timezone.utc)
        reporter_time = tlsrpt_utc_time_now()
        dt = reporter_time - receiver_time
        if abs(dt.total_seconds()) > self.cfg.max_receiver_timediff:
            logging.warning(f"Receiver time {receiver_time} and reporter time {reporter_time} differ more then "
                            f"{self.cfg.max_receiver_timediff} on fetcher {fetcherindex} {fetcher}")

        self.cur.execute("SAVEPOINT domainlist")
        # read the domain list
        result = True
        while True:
            dom = fetcherpipe.stdout.readline().decode('utf-8').rstrip()
            logging.debug("Got line %s", dom)
            if not dom:
                logging.warning("Unexpected end of domain list")
                result = False
                break
            if dom == ".":
                break
            try:
                self.cur.execute("INSERT INTO reportdata "
                                 "(day, domain, data, fetcherindex, fetcher, retries, status, nexttry) "
                                 "VALUES (?,?,NULL,?,?,0,NULL,?)",
                                 (day, dom, fetcherindex, fetcher, tlsrpt_utc_time_now()))
            except sqlite3.IntegrityError as e:
                logging.warning(e)
        if result:
            logging.info(f"DB-commit for fetcher {fetcherindex} {fetcher}")
            self.cur.execute("RELEASE SAVEPOINT domainlist")
            self.con.commit()
        else:
            logging.info(f"DB-rollback for fetcher {fetcherindex} {fetcher}")
            self.cur.execute("ROLLBACK TO SAVEPOINT domainlist")
            self.con.commit()
        return result

    def fetch_data(self):
        logging.debug("Fetch data")
        curtofetch = self.con.cursor()
        now = tlsrpt_utc_time_now()
        curtofetch.execute("SELECT day, fetcher, fetcherindex, domain FROM reportdata WHERE data IS NULL AND nexttry<?",
                           (now,))
        for row in curtofetch:
            self.fetch_data_from_fetcher_for_domain(row[0], row[1], row[2], row[3])

    def fetch_data_from_fetcher_for_domain(self, day, fetcher, fetcherindex, dom):
        logging.debug("Fetch data for domain %s from %d %s", dom, fetcherindex, fetcher)
        args = fetcher.split()
        args.append(day.__str__())
        args.append(dom)
        fetcherpipe = subprocess.Popen(args, stdout=subprocess.PIPE)
        alldata = fetcherpipe.stdout.read(TLSRPT_MAX_READ_FETCHER)
        print("WE HAVE READ FROM FETCHER DETAILS: ", alldata)
        j = json.loads(alldata)
        self.curtoupdate.execute("UPDATE reportdata SET data=? WHERE day=? AND fetcherindex=? AND domain=?",
                                 (json.dumps(j), day, fetcherindex, dom))
        self.con.commit()

    def create_reports(self):
        logging.debug("Create reports")
        curtofetch = self.con.cursor()
        self.curtoupdate = self.con.cursor()
        curtofetch.execute("SELECT fetcherindex, domain FROM reportdata WHERE data IS NULL")
        for row in curtofetch:
            logging.warning("Incomplete data for domain %s by fetcher index %d", row[1], row[0])
        print("TODO: aggregate and schedule reports")
        self.con.commit()

    def send_out_reports(self):
        logging.debug("Send out reports UNIMPLEMENTED")

    def wake_up_at(self, t):
        if self.wakeuptime > t:
            logging.debug(f"Changing wake up time from {self.wakeuptime} to {t}")
            self.wakeuptime = t
        else:
            logging.debug(f"Not changing wake up time from {self.wakeuptime} to {t}")

    def run_loop(self):
        while True:
            self.wakeuptime = tlsrpt_utc_time_now() + datetime.timedelta(seconds=60)
            self.check_day()
            self.collect_domains()
            self.fetch_data()
            self.create_reports()
            self.send_out_reports()
            dt = self.wakeuptime - tlsrpt_utc_time_now()
            seconds_to_sleep = dt.total_seconds()
            if seconds_to_sleep >= 0:
                logging.info("Sleeping for %d seconds", seconds_to_sleep)
                time.sleep(seconds_to_sleep)
            else:
                logging.info("Skipping sleeping for negative %d seconds", seconds_to_sleep)

# DELETEME/REVIEW: No used anywhere in the code. Should be removed
def myprint(*args, **kwargs):
    pass
    return print(*args, **kwargs)

# REVIEW: Should be used to utility module
def tlsrpt_utc_time_now():
    """
    Returns a timezone aware datetime object of the current UTC time.
    """
    return datetime.datetime.now().astimezone(datetime.timezone.utc)


# REVIEW: Should be used to utility module
def tlsrpt_utc_date_now():
    """
    Returns the current date in UTC.
    """
    return tlsrpt_utc_time_now().date()


# REVIEW: Should be used to utility module
def tlsrpt_utc_date_yesterday():
    """
    Returns the date of yesterday in UTC.
    """
    ts = tlsrpt_utc_time_now()   # Making sure, ts is timezone-aware and UTC.
    dt = datetime.timedelta(days=-1)
    return (ts + dt).date()


# REVIEW: config should be an argument, such that we can instantiate the
# dependency more easily (e.g. in test code to test differen configuration
# variants). A default argument might be useful here:
#
# def tlsrpt_receiver_main(config: ConfigReceiver=ConfigReceiver()):
def tlsrpt_receiver_main():
    """
    Contains the main TLSRPT receiver loop. This listens on a socket to
    receive TLSRPT datagrams from the MTA (e.g. Postfix). and writes the
    datagrams to the database.
    """
    config = ConfigReceiver()

    server_address = config.receiver_socketname

    logging.basicConfig(format="%(asctime)s %(levelname)s %(module)s %(lineno)s : %(message)s",
                        filename=config.receiver_logfilename, filemode="a", level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info("TLSRPT receiver starting")
    # Make sure the socket does not already exist
    try:
        if os.path.exists(server_address):
            os.unlink(server_address)
    except OSError as err:
        logging.error("Failed to remove already existing socket %s: %s", server_address, err)
        raise

    # Create a Unix Domain Socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    # Bind the socket to the port
    logging.info("Listening on socket %s" % server_address)
    sock.bind(server_address)
    sock.settimeout(config.receiver_sockettimeout)

    # Multiple receivers
    receivers = [DummyReceiver(False), TLSRPTReceiverSQLite(config)]

    while True:
        alldata = None  # clear old data to prevent accidentally processing it twice
        try:
            # Uncomment to test very low throughput
            # time.sleep(1)
            alldata, srcaddress = sock.recvfrom(TLSRPT_MAX_READ_RECEIVER)
            j = json.loads(alldata)
            for receiver in receivers:
                try:
                    receiver.add_datagram(j)
                except KeyError as err:
                    logging.error(f"KeyError {err} during processing datagram: {json.dumps(j)}")
                    raise err
        except socket.timeout:
            for receiver in receivers:
                receiver.socket_timeout()
        except OSError as err:
            print("Dummy error appened? WTF?")
            print(err)
            raise
        except UnicodeDecodeError as err:
            logging.error(f"Malformed utf8 data received: {err}")
        except json.decoder.JSONDecodeError as err:
            logging.error(f"JSON decode error: {err}")
            Path(config.dump_path_for_invalid_datagram).write_text(alldata.decode("utf-8"), encoding="utf-8")
        except sqlite3.OperationalError as err:
            logging.error(f"Database error: {err}")


# REVIEW: config should be an argument, such that we can instantiate the
# dependency more easily (e.g. in test code to test differen configuration
# variants). A default argument might be useful here:
#
# def tlsrpt_receiver_main(config: ConfigReceiver=ConfigReceiver()):
def tlsrpt_fetcher_main():
    """
    Runs the fetcher main. The fetcher is there to regularly consolidate the
    database entries that were written by the receiver.
    """
    # TLSRPT-fetcher is tightly coupled to TLSRPT-receiver and uses its config and database
    config = ConfigReceiver()

    logging.basicConfig(format="%(asctime)s %(levelname)s %(module)s %(lineno)s : %(message)s",
                        filename=config.fetcher_logfilename, filemode="a", level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())

    fetcher = TLSRPTFetcherSQLite(config)
    if len(sys.argv) < 2:
        print("Usage: %s day [domain]", file=sys.stderr)
        fetcher.fetch_domain_list(tlsrpt_utc_date_now())   # for testing just fetch
        sys.exit(1)
    if len(sys.argv) < 3:
        fetcher.fetch_domain_list(sys.argv[1])
    else:
        fetcher.fetch_domain_details(sys.argv[1], sys.argv[2])


# REVIEW: config should be an argument, such that we can instantiate the
# dependency more easily (e.g. in test code to test differen configuration
# variants). A default argument might be useful here:
#
# def tlsrpt_receiver_main(config: ConfigReceiver=ConfigReceiver()):
def tlsrpt_reporter_main():
    """
    Entry point to the reporter main. The reporter is the part that finally
    sends the STMP TLS reports out the endpoints that the other MTA operators
    have published.
    """
    config = ConfigReporter()
    logging.basicConfig(format="%(asctime)s %(levelname)s %(module)s %(lineno)s : %(message)s",
                        filename=config.reporter_logfilename, filemode="a", level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("TLSRPT reporter starting")

    reporter = TLSRPTReporter(config)
    reporter.run_loop()


if __name__ == "__main__":
    print("Call tlsrpt fetcher, receiver or reporter instead of this file", file=sys.stderr)
    print()
    while len(sys.argv) < 3:
        print("Expanding argv...")
        sys.argv.append("dummy")
    sys.argv[1] = str(tlsrpt_utc_date_now())
    sys.argv[2] = "test-0.exAmple.com"
    print("Now will do fetcher test-run !!! Args=", sys.argv)
    print()
    tlsrpt_fetcher_main()
