#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
"""turbineLiteDB.py
* Some functions to work directly with a local TurbineLite DB

John Eslick, Carnegie Mellon University, 2014
"""
import time
import uuid
import os
import threading
import adodbapi
import adodbapi.apibase

adodbapi.adodbapi.defaultCursorLocation = 2  # adodbapi.adUseServer


class DBException(Exception):
    pass


class keepAliveTimer(threading.Thread):
    def __init__(self, turbineDB, uid, freq=60):
        threading.Thread.__init__(self)
        self.stop = threading.Event()  # flag to stop thread
        self.freq = freq
        self.uid = uid
        self.db = turbineDB

    def terminate(self):
        self.stop.set()

    def run(self):
        i = 0
        while not self.stop.isSet():
            time.sleep(1)
            i += 1
            if i >= self.freq:
                self.db.consumer_keepalive(self.uid)
                i = 0


class turbineLiteDB:
    def __init__(self, close_after=True):
        self.conn = None
        self.close_after = close_after
        self.dbFile = (
            "C:\\Program Files (x86)"
            "\\Turbine\\Lite\\Data\\TurbineCompactDatabase.sdf"
        )

    def __del__(self):
        self.closeConnection()

    def connectionString(self):
        prov = "Provider=Microsoft.SQLSERVER.CE.OLEDB.4.0;"
        data = "Data Source={0};".format(self.dbFile)
        return " ".join([prov, data])

    def getConnection(self, rc=0):
        if self.conn is not None:
            return self.conn, self.conn.cursor()
        try:
            conn = adodbapi.connect(self.connectionString(), autocommit=True)
            self.conn = conn
        except Exception as e:
            if rc <= 5:
                time.sleep(10 * rc**2)
                conn, curs = self.getConnection(rc + 1)
            else:
                raise (e)
        return conn, conn.cursor()

    def closeConnection(self):
        if self.conn is None:
            return
        try:
            self.conn.close()
            self.conn = None
        except:
            self.conn = None

    def add_new_application(self, applicationName, rc=0):
        """
        Turbine Consumer Function
        ---
        Add an application type to the TurbineLite database

        args

        return value
        """
        conn, curs = self.getConnection()
        try:
            sqlstr = "SELECT Name FROM Applications WHERE Name='{0}'".format(
                applicationName
            )
            curs.execute(sqlstr)
            if curs.fetchone() is None:
                sqlstr = "INSERT INTO Applications VALUES ('{0}', NULL, NULL)".format(
                    applicationName
                )
                curs.execute(sqlstr)
            self.closeConnection()
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.add_new_application(applicationName, rc=rc + 1)

    def add_message(self, msg, jobid, rc=0):
        conn, curs = self.getConnection()
        try:
            uid = str(uuid.uuid4())
            t = time.strftime("%m/%d/%Y %I:%M %p", time.gmtime())
            sqlstr = "INSERT INTO Messages VALUES ('{0}', '{1}', '{2}', '{3}')".format(
                uid, msg, t, jobid
            )
            curs.execute(sqlstr)
            self.closeConnection()
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.add_message(msg, jobid, rc=rc + 1)

    def consumer_keepalive(self, uid, rc=0):
        conn, curs = self.getConnection()
        try:
            t = time.strftime("%m/%d/%Y %I:%M %p", time.gmtime())
            sqlstr = "UPDATE JobConsumers SET keepalive='{0}' WHERE Id='{1}'".format(
                t, uid
            )
            curs.execute(sqlstr)
            self.closeConnection()
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.consumer_keepalive(uid, rc=rc + 1)

    def consumer_status(self, uid, status=None, rc=0):
        conn, curs = self.getConnection()
        try:
            if status is not None:
                sqlstr = "UPDATE JobConsumers SET status='{0}' WHERE Id='{1}'".format(
                    status, uid
                )
                curs.execute(sqlstr)
                self.closeConnection()
            else:
                sqlstr = "SELECT status FROM JobConsumers WHERE Id='{0}'".format(uid)
                curs.execute(sqlstr)
                s = curs.fetchone()
                self.closeConnection()
                if s == None:
                    return None
                return s[0]
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.consumer_status(uid, status, rc=rc + 1)

    def consumer_id(self, pid, rc=0):
        conn, curs = self.getConnection()
        try:
            sqlstr = "SELECT Id FROM JobConsumers WHERE processId='{0}' AND status='up'".format(
                pid
            )
            curs.execute(sqlstr)
            s = curs.fetchone()
            self.closeConnection()
            if s == None:
                return None
            return s[0]
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.consumer_id(pid, rc=rc + 1)

    def consumer_register(self, rc=0):
        conn, curs = self.getConnection()
        try:
            uid = str(uuid.uuid4())
            t = time.strftime("%m/%d/%Y %I:%M %p", time.gmtime())
            sqlstr = (
                "INSERT INTO JobConsumers "
                "VALUES "
                "('{0}', 'localhost', {1}, 'up', '{2}', 'foqus')".format(
                    uid, os.getpid(), t
                )
            )
            curs.execute(sqlstr)
            self.closeConnection()
            return uid
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.consumer_register(rc=rc + 1)

    def get_job_id(
        self, simName=None, sessionID=None, consumerID=None, state="submit", rc=0
    ):
        """
        Turbine Consumer Function, get first job with submit status
        and is the foqus application type
        ---
        Desc

        args

        return value
        """
        conn, curs = self.getConnection()
        try:
            sqlstr = (
                "SELECT TOP 1 Jobs.Id, Jobs.Count, Jobs.SimulationId, Jobs.Reset"
                " FROM Jobs INNER JOIN Simulations"
                " ON Jobs.SimulationId=Simulations.Id"
                " WHERE "
                " Jobs.State='{0}' "
                " AND Simulations.ApplicationName='foqus'".format(state)
            )
            if sessionID is not None:
                sqlstr += " AND Jobs.SessionId='{0}'".format(sessionID)
            if simName is not None:
                sqlstr += " AND Simulations.Name='{0}'".format(simName)
            if consumerID is not None:
                sqlstr += " AND Jobs.ConsumerId='{0}'".format(consumerID)
            curs.execute(sqlstr)
            row = curs.fetchone()
            self.closeConnection()
            if row is not None:
                jobsGUID = row[0].strip("{}")
                jobsID = row[1]
                simID = row[2].strip("{}")
                reset = row[3]
                if not reset or reset == "false":
                    reset = False
                else:
                    reset = True
                return jobsGUID, jobsID, simID, reset
            return None, None, None, None
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.get_job_id(simName, sessionID, consumerID, state, rc=rc + 1)

    def jobConsumerID(self, jid, cid=None, rc=0):
        """
        Get or set job consumer ID
        """
        conn, curs = self.getConnection()
        try:
            if cid is None:
                # get the job's consumer ID
                sqlstr = "SELECT ConsumerId FROM Jobs WHERE Id='{0}'".format(jid)
                curs.execute(sqlstr)
                row = curs.fetchone()
                self.closeConnection()
                if row is None:
                    cid = None
                else:
                    cid = row[0].strip("{}")
            else:
                # set the job's consumer ID
                sqlstr = "UPDATE Jobs SET ConsumerId='{0}' WHERE Id='{1}'".format(
                    cid, jid
                )
                curs.execute(sqlstr)
                self.closeConnection()
            return cid
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.jobConsumerID(jid, cid, rc=rc + 1)

    def get_configuration_file(self, simulationId, rc=0):
        """
        Turbine Consumer Function
        ---
        Desc

        args

        return value
        """
        conn, curs = self.getConnection()
        try:
            sqlstr = (
                "SELECT Content FROM SimulationStagedInputs "
                "WHERE SimulationId='{0}'".format(simulationId)
            )
            curs.execute(sqlstr)
            row = curs.fetchone()
            self.closeConnection()
            if row is None:
                return None
            return row[0].decode("utf-8")
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.get_configuration_file(simulationId, rc=rc + 1)

    def job_prepare(self, jobGuid, jobId, configFile, rc=0):
        """
        Turbine Consumer Function
        ---
        Write input values file to run FOQUS job

        args

        return value
        """
        conn, curs = self.getConnection()
        try:
            sqlstr = "SELECT Input FROM Processes WHERE Id='{0}'".format(jobGuid)
            curs.execute(sqlstr)
            row = curs.fetchone()
            self.closeConnection()
            jobPath = "test/{0}".format(jobId)
            if not os.path.exists("test"):
                os.makedirs("test")
            if not os.path.exists(jobPath):
                os.makedirs(jobPath)
            ifile = os.path.join(jobPath, "input_values.json")
            cfile = os.path.join(jobPath, "session.foqus")
            if row is not None:
                assert configFile is not None, "Missing configFile"
                headerStr = '{"input":'
                footerStr = "}"
                with open(ifile, "w") as text_file:
                    text_file.write("".join([headerStr, row[0], footerStr]))
                with open(cfile, "w") as config_file:
                    config_file.write(configFile)
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.job_prepare(jobGuid, jobId, configFile, rc=rc + 1)

    def job_change_status(self, jobGuid, status, rc=0):
        """
        Turbine Consumer Function
        ---
        Change the status of a Turbine FOQUS job

        args

        return value
        """
        conn, curs = self.getConnection()
        try:
            t = time.strftime("%m/%d/%Y %I:%M %p", time.gmtime())
            sqlstr = "UPDATE Jobs SET State='{0}' WHERE Id='{1}'".format(
                status, jobGuid
            )
            curs.execute(sqlstr)
            if status == "setup":
                sqlstr = "UPDATE Jobs SET Setup='{0}' WHERE Id='{1}'".format(t, jobGuid)
                curs.execute(sqlstr)
            elif status == "running":
                sqlstr = "UPDATE Jobs SET Running='{0}' WHERE Id='{1}'".format(
                    t, jobGuid
                )
                curs.execute(sqlstr)
            elif status in ["success", "error", "terminate", "cancel"]:
                sqlstr = "UPDATE Jobs SET Finished='{0}' WHERE Id='{1}'".format(
                    t, jobGuid
                )
                curs.execute(sqlstr)
            self.closeConnection()
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.job_change_status(jobGuid, status, rc=rc + 1)

    def job_save_output(self, jobGuid, workingDir, rc=0):
        """
        Turbine Consumer Function
        ---
        Put job output in the databae

        args

        return value
        """
        conn, curs = self.getConnection()
        try:
            with open(os.path.join(workingDir, "output.json")) as outfile:
                output = outfile.read()
            sqlstr = "UPDATE Processes SET Output='{0}' WHERE Id='{1}'".format(
                output, jobGuid
            )
            curs.execute(sqlstr)
            self.closeConnection()
        except Exception as e:
            self.closeConnection()
            if rc > 1:
                raise e
            else:
                self.job_save_output(jobGuid, workingDir, rc=rc + 1)
