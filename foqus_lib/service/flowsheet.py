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
"""flowsheet.py
* The AWS Cloud FOQUS service to start FOQUS

Joshua Boverhof, Lawrence Berkeley National Lab

"""
import socket
import os
import time
import boto3, optparse
import sys, json, signal, os, errno, uuid, threading, time, traceback
from os.path import expanduser
import urllib.request, urllib.error, urllib.parse
from foqus_lib.framework.session.session import session as Session
from foqus_lib.framework.session.session import generalSettings as FoqusSettings
from foqus_lib.framework.graph.nodeVars import NodeVarListEx, NodeVarEx
from foqus_lib.framework.foqusException.foqusException import *
from foqus_lib.framework.graph.graph import Graph
from foqus_lib.framework.plugins import pluginSearch
from foqus_lib.framework.pymodel import pymodel
from turbine.commands import turbine_simulation_script
import logging
import logging.config
import botocore.exceptions

WORKING_DIRECTORY = os.path.abspath(
    os.environ.get("FOQUS_SERVICE_WORKING_DIR", "\\ProgramData\\foqus_service")
)
DEBUG = False
CURRENT_JOB_DIR = None
_log = logging.getLogger("foqus.foqus_lib.service.flowsheet")


def _set_working_dir(wdir):
    global _log, WORKING_DIRECTORY
    WORKING_DIRECTORY = wdir
    log_dir = os.path.join(wdir, "logs")
    try:
        os.makedirs(log_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    os.chdir(wdir)
    FoqusSettings().applyLogSettings()

    _log = logging.getLogger("foqus.foqus_lib.service.flowsheet")
    _log.setLevel(logging.DEBUG)
    _log.info("Working Directory: %s", WORKING_DIRECTORY)
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)


def _get_user_config_location(*args, **kw):
    _log.debug("USER CONFIG: %s", str(args))
    return os.path.join(WORKING_DIRECTORY, "foqus.cfg")


FoqusSettings.getUserConfigLocation = _get_user_config_location


def getfilenames(jid):
    global CURRENT_JOB_DIR
    CURRENT_JOB_DIR = os.path.join(WORKING_DIRECTORY, str(jid))

    _log.info("Job Directory: %s", CURRENT_JOB_DIR)
    try:
        os.makedirs(CURRENT_JOB_DIR)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    sfile = os.path.join(CURRENT_JOB_DIR, "session.foqus")
    # result session file to keep on record
    rfile = os.path.join(CURRENT_JOB_DIR, "results_session.foqus")
    # Input values files
    vfile = os.path.join(CURRENT_JOB_DIR, "input_values.json")
    # Output values file
    ofile = os.path.join(CURRENT_JOB_DIR, "output.json")
    return sfile, rfile, vfile, ofile


def scrub_empty_string_values_for_dynamo(db):
    """DynamoDB throws expection if there is an empty string in dict
    ValidationException: ExpressionAttributeValues contains invalid value:
    One or more parameter values were invalid: An AttributeValue may not contain an empty string for key :o
    """
    if type(db) is not dict:
        return
    for k, v in list(db.items()):
        if v in ("", ""):
            db[k] = "NULL"
        else:
            scrub_empty_string_values_for_dynamo(v)


def _setup_foqus_user_plugin(dat, nkey, user_name, user_plugin_dir):
    assert len(dat.flowsheet.nodes[nkey].turbApp) == 2, (
        "DAT Flowsheet nodes turbApp is %s" % dat.flowsheet.nodes[nkey].turbApp
    )
    node = dat.flowsheet.nodes[nkey]
    turb_app = node.turbApp[0]
    model_name = node.modelName
    assert turb_app is not None
    turb_app = turb_app.lower()
    assert turb_app == "foqus-user-plugin", 'unknown foqus-user-plugin: "%s"' % turb_app
    _log.debug(
        'Turbine Node Key="%s", Model="%s", Application="%s"',
        nkey,
        model_name,
        turb_app,
    )
    model_user_plugin_dir = os.path.join(user_plugin_dir, model_name)
    try:
        os.makedirs(model_user_plugin_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    s3 = boto3.client("s3", region_name=FOQUSAWSConfig.get_instance().get_region())
    bucket_name = FOQUSAWSConfig.get_instance().get_simulation_bucket_name()
    prefix = "%s/%s/" % (user_name, model_name)
    l = s3.list_objects(Bucket=bucket_name, Prefix=prefix)

    assert (
        "Contents" in l
    ), 'Node %s failure: S3 Bucket %s is missing simulation files for "%s"' % (
        nkey,
        bucket_name,
        prefix,
    )
    key_sinter_filename = None
    key_plugin_filename = None
    s3_key_list = [i["Key"] for i in l["Contents"]]
    _log.debug("Node model %s staged-input files %s" % (model_name, s3_key_list))

    for k in s3_key_list:
        if k.endswith("/foqus-user-plugin.json"):
            key_sinter_filename = k
        elif k.endswith("/%s.py" % (model_name)):
            assert key_plugin_filename is None, "detected multiple plugin files"
            key_plugin_filename = k

    assert (
        key_sinter_filename is not None
    ), "Flowsheet node=%s simulation=%s sinter configuration not in %s" % (
        nkey,
        model_name,
        str(s3_key_list),
    )
    assert (
        key_plugin_filename is not None
    ), "Flowsheet node=%s simulation=%s model file not in %s" % (
        nkey,
        model_name,
        str(s3_key_list),
    )

    entry_list = [
        i for i in l["Contents"] if i["Key"] != prefix and i["Key"].startswith(prefix)
    ]
    for entry in entry_list:
        _log.debug("s3 staged input: %s", entry)
        key = entry["Key"]
        etag = entry.get("ETag", "").strip('"')
        target_file_path = None
        assert key.startswith(prefix)
        if key == key_sinter_filename:
            target_file_path = os.path.join(model_user_plugin_dir, key.split("/")[-1])
            s3.download_file(bucket_name, key, target_file_path)
        elif key == key_plugin_filename:
            target_file_path = os.path.join(user_plugin_dir, key.split("/")[-1])
            s3.download_file(bucket_name, key, target_file_path)
        else:
            args = [i for i in key[len(prefix) :].split("/") if i]
            args.insert(0, model_user_plugin_dir)
            target_file_path = os.path.join(*args)
            s3.download_file(bucket_name, key, target_file_path)

        _log.debug(
            'model="%s" key="%s" staged-in file="%s"'
            % (model_name, key, target_file_path)
        )


def _setup_flowsheet_turbine_node(dat, nkey, user_name):
    """From s3 download all simulation files into AspenSinterComsumer cache directory '{working_directory\test\{simulation_guid}'.  If
    Simulation does not exist create one.  If Simulation does exist just s3 download all simulation files into the above cache directory.

    The new simulation_guid is created for all file updates to TurbineWS, so this is sidestepping that process.

    TODO: Provide a simulation_id via S3 ( eg.  {simulation_name}/Id )

    """
    assert len(dat.flowsheet.nodes[nkey].turbApp) == 2, (
        "DAT Flowsheet nodes turbApp is %s" % dat.flowsheet.nodes[nkey].turbApp
    )
    node = dat.flowsheet.nodes[nkey]
    turb_app = node.turbApp[0]
    model_name = node.modelName
    assert turb_app is not None
    turb_app = turb_app.lower()
    assert turb_app in ["acm", "aspenplus"], (
        'unknown turbine application "%s"' % turb_app
    )
    _log.debug(
        'Turbine Node Key="%s", Model="%s", Application="%s"',
        nkey,
        model_name,
        turb_app,
    )

    """ Search S3 Bucket for node simulation
    """
    s3 = boto3.client("s3", region_name=FOQUSAWSConfig.get_instance().get_region())
    bucket_name = FOQUSAWSConfig.get_instance().get_simulation_bucket_name()
    prefix = "%s/%s/" % (user_name, model_name)
    l = s3.list_objects(Bucket=bucket_name, Prefix=prefix)
    assert (
        "Contents" in l
    ), 'Node %s failure: S3 Bucket %s is missing simulation files for "%s"' % (
        nkey,
        bucket_name,
        prefix,
    )
    key_sinter_filename = None
    key_model_filename = None
    s3_key_list = [i["Key"] for i in l["Contents"]]
    _log.debug("Node model %s staged-input files %s" % (model_name, s3_key_list))
    for k in s3_key_list:
        if k.endswith("/%s_sinter.json" % turb_app):
            key_sinter_filename = k
        elif turb_app == "acm" and k.endswith(".acmf"):
            assert key_model_filename is None, "detected multiple model files"
            key_model_filename = k
        elif turb_app == "aspenplus" and k.endswith(".bkp"):
            assert key_model_filename is None, "detected multiple model files"
            key_model_filename = k

    assert (
        key_sinter_filename is not None
    ), "Flowsheet node=%s simulation=%s sinter configuration not in %s" % (
        nkey,
        model_name,
        str(s3_key_list),
    )
    assert (
        key_model_filename is not None
    ), "Flowsheet node=%s simulation=%s model file not in %s" % (
        nkey,
        model_name,
        str(s3_key_list),
    )

    """ search TurbineLite WS for node simulation
    """
    print(turbine_simulation_script.__file__)
    turbine_cfg = node.gr.turbConfig.getFile()
    _log.debug("CWD: %s", os.path.abspath(os.path.curdir))
    turbine_cfg = os.path.abspath(turbine_cfg)
    _log.debug("Turbine Configuration File: %s", turbine_cfg)
    sim_list = turbine_simulation_script.main_list([turbine_cfg], func=None)
    print("Simulation List %s" % sim_list)
    sim_d = [i for i in sim_list if i["Name"] == model_name]
    cache_sim_guid = None
    assert len(sim_d) < 2, "Expecting 0 or 1 entries for simulation %s" % model_name
    if len(sim_d) == 0:
        _log.debug('No simulation="%s" in TurbineLite' % model_name)
        sim_d = None
        cache_sim_guid = str(uuid.uuid4())
    else:
        _log.debug('Found simulation="%s" in TurbineLite' % model_name)
        sim_d = sim_d[0]
        assert "Id" in sim_d, "Missing keys in Simulation %s" % sim_d
        cache_sim_guid = sim_d["Id"]

    """ upload all staged-inputs to TurbineLite if new or updated in
    s3://{bucketname}/{username}/{simulation}
    """
    entry_list = [
        i for i in l["Contents"] if i["Key"] != prefix and i["Key"].startswith(prefix)
    ]
    update_required = False
    # target_dir = os.path.join(CURRENT_JOB_DIR, model_name)
    target_dir = os.path.join(WORKING_DIRECTORY, "test", cache_sim_guid)
    os.makedirs(target_dir, exist_ok=True)
    sinter_local_filename = None
    for entry in entry_list:
        _log.debug("s3 staged input: %s", entry)
        key = entry["Key"]
        etag = entry.get("ETag", "").strip('"')
        # Upload to TurbineLite
        # if ends with json or acmf
        si_metadata = []
        target_file_path = None
        assert key.startswith(prefix)
        if key == key_sinter_filename:
            # assert key_sinter_filename == '/'.join(prefix, key_sinter_filename.split('/')[-1]), \
            #    'sinter configuration "%s" must be in model base directory: "%s"' %(key_model_filename,prefix)
            target_file_path = os.path.join(target_dir, "sinter_configuration.txt")
            sinter_local_filename = target_file_path
            if sim_d:
                si_metadata = [
                    i for i in sim_d["StagedInputs"] if i["Name"] == "configuration"
                ]
            s3.download_file(bucket_name, key, target_file_path)
        elif key == key_model_filename:
            # assert key_model_filename == '/'.join(prefix, key_model_filename.split('/')[-1]), \
            #    'sinter configuration "%s" must be in model base directory: "%s"' %(key_model_filename,prefix)
            target_file_path = os.path.join(target_dir, key.split("/")[-1])
            if sim_d:
                si_metadata = [
                    i for i in sim_d["StagedInputs"] if i["Name"] == "aspenfile"
                ]
            s3.download_file(bucket_name, key, target_file_path)
        else:
            args = [i for i in key[len(prefix) :].split("/") if i]
            args.insert(0, target_dir)
            target_file_path = os.path.join(*args)
            if sim_d:
                si_metadata = [
                    i for i in sim_d["StagedInputs"] if i["Name"] == key.split("/")[-1]
                ]
            s3.download_file(bucket_name, key, target_file_path)

        _log.debug(
            'model="%s" key="%s" staged-in file="%s"'
            % (model_name, key, target_file_path)
        )
        assert (
            len(si_metadata) < 2
        ), 'Turbine Error:  Duplicate entries for "%s", "%s"' % (model_name, key)
        """NOTE: Multipart uploads have different ETags ( end with -2  or something )
        Thus the has comparison will fail.  For now ignore it, but fixing this check is performance optimization.

        if len(si_metadata) == 1:
            file_hash = si_metadata[0]['MD5Sum']
            if file_hash.lower() != etag.lower():
                _log.debug('Updated detected(hash "%s" != "%s"):  s3.getObject "%s"' %(etag,file_hash,key))
                s3.download_file(bucket_name, key, target_file_path)
                update_required = True
            else:
                _log.debug('md5 matches for staged-in file "%s"' %key)
        else:
            _log.debug('Add to Turbine Simulation(%s) s3.getObject: "%s"' %(model_name, key))
            s3.download_file(bucket_name, key, target_file_path)
            update_required = True
        """

    assert sinter_local_filename is not None, "missing sinter configuration file"

    if sim_d is None:
        _log.debug('Adding Simulation "%s" "%s"' % (model_name, cache_sim_guid))
        node.gr.turbConfig.uploadSimulation(
            model_name, sinter_local_filename, guid=cache_sim_guid, update=False
        )
    """
    elif update_required:
        # NOTE: Requires the configuration file on update, so must download_file it above...
        _log.debug('Updating Simulation "%s"' %model_name)
        node.gr.turbConfig.uploadSimulation(model_name, sinter_local_filename, update=True)
        _log.debug(
    else:
        _log.debug('No Update Required for Simulation "%s"' %model_name)

    """


class FOQUSJobException(Exception):
    """Custom Exception for holding onto the job description and user name"""

    def __init__(self, message, job_desc, user_name):
        super().__init__(message)
        self.job_desc = job_desc
        self.user_name = user_name


class FOQUSAWSConfig:
    """
    { example:
      "FOQUS-Update-Topic-Arn": "arn:aws:sns:us-west-2:387057575688:FoqusCloudStack-bluejobtopicidA63AF7BE-NY5APVGJL24B",
      "FOQUS-Message-Topic-Arn": "arn:aws:sns:us-west-2:387057575688:FoqusCloudStack-bluelogtopicid50E21335-PBVQAP0RYZ5D",
      "FOQUS-Job-Queue-Url": "arn:aws:sqs:us-west-2:387057575688:FoqusCloudUserStack-blueboverhofqueueidEDBC6161-zgo4wkNousqm",
      "FOQUS-Simulation-Bucket-Name": "arn:aws:s3:::foquscloudstack-bluefoqussimulation99ec6532-170r4pwindi5n",
      "FOQUS-Session-Bucket-Name": "arn:aws:s3:::foquscloudstack-bluefoqussession99ec6532-170r4pwindi5n",
      "FOQUS-User": "boverhof"
    }
    """

    _inst = None

    @classmethod
    def get_instance(cls):
        if cls._inst is not None:
            return cls._inst
        # request = urllib.request.urlopen("http://169.254.169.254/latest/user-data")
        inst = cls()
        inst._d = d = dict()
        try:
            region = urllib.request.urlopen(
                "http://169.254.169.254/latest/meta-data/placement/region"
            ).read()
            inst.region = region.decode("ascii")
            instance_id = urllib.request.urlopen(
                "http://169.254.169.254/latest/meta-data/instance-id"
            ).read()
            inst.instance_id = instance_id.decode("ascii")
            tags = urllib.request.urlopen(
                "http://169.254.169.254/latest/meta-data/tags/instance"
            ).read()
            for tag in tags.decode("ascii").split():
                url = "http://169.254.169.254/latest/meta-data/tags/instance/%s" % (tag)
                value = urllib.request.urlopen(url).read()
                d[tag] = value.decode("ascii")
        except Exception as ex:
            _log.error("Failed to discover instance-id or tag FoqusUser: %s", repr(ex))
            raise
        # Validate
        try:
            inst.get_region()
            inst.get_user()
            inst.get_update_topic_arn()
            inst.get_message_topic_arn()
            inst.get_job_queue_url()
            inst.get_simulation_bucket_name()
            inst.get_session_bucket_name()
            inst.get_dynamo_table_name()
        except Exception as ex:
            _log.error("Missing Tag: %s", repr(ex))
            raise

        cls._inst = inst
        return cls._inst

    def __init__(self):
        self._d = None

    def _get(self, key):
        v = self._d.get(key)
        assert v, "UserData/MetaData Missing Key(%s): %s" % (key, str(self._d))
        _log.debug("FOQUSAWSConfig._get: %s = %s" % (key, v))
        return v

    def get_region(self):
        return self.region

    def get_instance_id(self):
        return self.instance_id

    def get_user(self):
        return self._get("FOQUS-User")

    def get_update_topic_arn(self):
        return self._get("FOQUS-Update-Topic-Arn")

    def get_message_topic_arn(self):
        return self._get("FOQUS-Message-Topic-Arn")

    def get_alert_topic_arn(self):
        return self._get("FOQUS-Alert-Topic-Arn")

    def get_job_queue_url(self):
        return self._get("FOQUS-Job-Queue-Url")

    def get_simulation_bucket_name(self):
        return self._get("FOQUS-Simulation-Bucket-Name")

    def get_session_bucket_name(self):
        return self._get("FOQUS-Session-Bucket-Name")

    def get_dynamo_table_name(self):
        return self._get("FOQUS-DynamoDB-Table")


class _KeepAliveTimer(threading.Thread):
    def __init__(self, turbineDB, freq=60):
        threading.Thread.__init__(self)
        self.stop = threading.Event()  # flag to stop thread
        self.freq = freq
        self.db = turbineDB
        self.daemon = True

    def terminate(self):
        self.stop.set()

    def run(self):
        i = 0
        while not self.stop.isSet():
            time.sleep(1)
            i += 1
            if i >= self.freq:
                self.db.consumer_keepalive()
                i = 0


class TurbineLiteDB:
    """ """

    def __init__(self, close_after=True):
        self._topic_arn = FOQUSAWSConfig.get_instance().get_update_topic_arn()
        self._topic_msg_arn = FOQUSAWSConfig.get_instance().get_message_topic_arn()
        self._user_name = FOQUSAWSConfig.get_instance().get_user()
        self._sns = boto3.client(
            "sns", region_name=FOQUSAWSConfig.get_instance().get_region()
        )
        self.consumer_id = str(uuid.uuid4())

    def _sns_notification(self, obj):
        _log.debug("_sns_notification obj: %s" % obj)
        resource = obj.get("resource", "unknown")
        status = obj.get("status", "unknown")
        if resource == "consumer":
            status = obj.get("event", "unknown")
        event = "%s.%s" % (resource, status)
        _log.debug("_sns_notification event: %s" % event)
        attrs = dict(
            event=dict(DataType="String", StringValue=event),
            username=dict(DataType="String", StringValue=self._user_name),
        )
        _log.debug("MessageAttributes: %s" % attrs)
        self._sns.publish(
            Message=json.dumps([obj]), MessageAttributes=attrs, TopicArn=self._topic_arn
        )

    def __del__(self):
        _log.info("%s.delete", self.__class__.__name__)

    def authorize_user_name(self, name):
        if name != self._user_name:
            return False
        self._user_name = name
        return True

    def connectionString(self):
        _log.info("%s.connectionString", self.__class__.__name__)

    def getConnection(self, rc=0):
        _log.info("%s.getConnection", self.__class__.__name__)

    def closeConnection(self):
        _log.info("%s.closeConnection", self.__class__.__name__)

    def add_new_application(self, applicationName, rc=0):
        _log.info("%s.add_new_application", self.__class__.__name__)

    def add_message(self, msg, jobid="", **kw):
        d = dict(
            job=jobid,
            message=msg,
            consumer=self.consumer_id,
            instanceid=FOQUSAWSConfig.get_instance().get_instance_id(),
            resource="job",
        )
        d.update(kw)
        obj = json.dumps(d)
        _log.debug("%s.add_message: %s", self.__class__.__name__, obj)
        self._sns.publish(Message=obj, TopicArn=self._topic_msg_arn)

    def consumer_keepalive(self, rc=0):
        _log.info("%s.consumer_keepalive", self.__class__.__name__)
        self._sns_notification(
            dict(
                resource="consumer",
                event="running",
                rc=rc,
                consumer=self.consumer_id,
                instanceid=FOQUSAWSConfig.get_instance().get_instance_id(),
            )
        )

    def consumer_status(self):
        _log.info("%s.consumer_status", self.__class__.__name__)
        # assert status in ['up','down','terminate'], ''
        # self._sns_notification(dict(resource='consumer', event=status, rc=rc, consumer=self.consumer_id))
        return "up"

    def consumer_id(self, pid, rc=0):  # TODO pylint: disable=method-hidden
        _log.info("%s.consumer_id", self.__class__.__name__)

    def consumer_register(self, rc=0):
        _log.info("%s.consumer_register", self.__class__.__name__)
        d = dict(
            resource="consumer",
            instanceid=FOQUSAWSConfig.get_instance().get_instance_id(),
            event="running",
            rc=rc,
            consumer=self.consumer_id,
        )
        self._sns_notification(d)
        _log.info("%s.consumer_register: %s", self.__class__.__name__, str(d))

    # def get_job_id(self, simName=None, sessionID=None, consumerID=None, state='submit', rc=0):
    #    _log.info("%s.get_job_id", self.__class__)
    #    return guid, jid, simId, reset

    def jobConsumerID(self, jid, cid=None, rc=0):
        _log.info("%s.jobConsumerID", self.__class__.__name__)

    def get_configuration_file(self, simulationId, rc=0):
        _log.info("%s.get_configuration_file", self.__class__.__name__)

    def job_prepare(self, jobGuid, jobId, configFile, rc=0):
        _log.info("%s.job_prepare", self.__class__.__name__)

    def job_change_status(self, job_d, status, rc=0, message=None):
        assert type(job_d) is dict
        assert status in [
            "success",
            "setup",
            "running",
            "error",
            "terminate",
            "expired",
            "invalid",
        ], (
            "Incorrect Job Status %s" % status
        )
        _log.info("%s.job_change_status %s", self.__class__.__name__, job_d)
        d = dict(
            resource="job",
            event="status",
            rc=rc,
            status=status,
            jobid=job_d["Id"],
            instanceid=FOQUSAWSConfig.get_instance().get_instance_id(),
            consumer=self.consumer_id,
            sessionid=job_d.get("sessionid", "unknown"),
        )
        if message:
            d["message"] = message
        self._sns_notification(d)

    def job_save_output(self, job_d, workingDir, rc=0):
        """Save simulation output.  This is published to SNS, need to wait
        for tables to update before changing status to "success" or "error"
        otherwise "output" is occasionally not available yet.
        """
        assert type(job_d) is dict
        _log.info("%s.job_save_output", self.__class__.__name__)
        with open(os.path.join(workingDir, "output.json")) as outfile:
            output = json.load(outfile)
        scrub_empty_string_values_for_dynamo(output)
        _log.debug(
            "%s.job_save_output:  %s", self.__class__.__name__, json.dumps(output)
        )
        self._sns_notification(
            dict(
                resource="job",
                event="output",
                jobid=job_d["Id"],
                username=self._user_name,
                value=output,
                rc=rc,
                sessionid=job_d.get("sessionid", "unknown"),
            )
        )


def _publish_service_error(message="", detail=""):
    """Publish to SNS Message Topic with MessageAttributes
    instance and event to filter for alerting.
    Arguments:
        message:
    """
    topic_alert_arn = FOQUSAWSConfig.get_instance().get_alert_topic_arn()
    instance_id = FOQUSAWSConfig.get_instance().get_instance_id()
    _log.error("publish(%s) service error: %s", topic_alert_arn, message)
    sns = boto3.client("sns", region_name=FOQUSAWSConfig.get_instance().get_region())
    attrs = dict(
        event=dict(DataType="String", StringValue="service.error"),
        instance=dict(DataType="String", StringValue=instance_id),
    )
    d = dict(
        message=message, detail=detail, instance=instance_id, event="service.error"
    )
    sns.publish(
        Message=json.dumps(d), MessageAttributes=attrs, TargetArn=topic_alert_arn
    )
    _log.info("published")


class FlowsheetControl:
    """API for controlling Flowsheet process
    from foqus_lib.service.flowsheet import FlowsheetControl;
    fc = FlowsheetControl();
    fc.run()"
    """

    _is_set_working_directory = False

    def __init__(self):
        """
        _dat -- Session
        _kat -- keepAliveTimer
        """
        self._metric_count_of_queue_peeks = 0
        self._metric_count_of_job_finished_dict = dict()
        self._set_working_directory()
        socket.setdefaulttimeout(60)
        self._dat = None
        self._kat = None
        self._stop = False
        self._receipt_handle = None
        self._simulation_name = None
        self._queue_url = FOQUSAWSConfig.get_instance().get_job_queue_url()
        self._sqs = boto3.client(
            "sqs", region_name=FOQUSAWSConfig.get_instance().get_region()
        )
        self._dynamodb = boto3.client(
            "dynamodb", region_name=FOQUSAWSConfig.get_instance().get_region()
        )
        self._dynamodb_table_name = (
            FOQUSAWSConfig.get_instance().get_dynamo_table_name()
        )
        self._cloudwatch = boto3.client(
            "cloudwatch", region_name=FOQUSAWSConfig.get_instance().get_region()
        )

    @classmethod
    def _set_working_directory(cls, working_dir=WORKING_DIRECTORY):
        if cls._is_set_working_directory:
            return
        _set_working_dir(working_dir)
        cls._is_set_working_directory = True

    def stop(self):
        self._stop = True

    def increment_metric_job_finished(self, event):
        if not event in self._metric_count_of_job_finished_dict:
            self._metric_count_of_job_finished_dict[event] = 0
        self._metric_count_of_job_finished_dict[event] += 1
        self._cloudwatch.put_metric_data(
            Namespace="foqus-cloud-backend",
            MetricData=[
                {
                    "MetricName": "count_of_job_finish",
                    "Dimensions": [
                        {
                            "Name": "user_name",
                            "Value": FOQUSAWSConfig.get_instance().get_user(),
                        },
                        {
                            "Name": "instance_id",
                            "Value": FOQUSAWSConfig.get_instance().get_instance_id(),
                        },
                        {"Name": "event", "Value": event},
                    ],
                    "Value": self._metric_count_of_job_finished_dict[event],
                    "Unit": "Count",
                },
            ],
        )

    def increment_metric_queue_peeks(self, state, reset=False):
        if reset:
            self._metric_count_of_queue_peeks = dict()
        if not state in self._metric_count_of_queue_peeks:
            self._metric_count_of_queue_peeks[state] = 0
        if not reset:
            self._metric_count_of_queue_peeks[state] += 1

        self._cloudwatch.put_metric_data(
            Namespace="foqus-cloud-backend",
            MetricData=[
                {
                    "MetricName": "count_of_queue_peeks",
                    "Dimensions": [
                        {
                            "Name": "user_name",
                            "Value": FOQUSAWSConfig.get_instance().get_user(),
                        },
                        {
                            "Name": "instance_id",
                            "Value": FOQUSAWSConfig.get_instance().get_instance_id(),
                        },
                        {"Name": "state", "Value": state},
                    ],
                    "Value": self._metric_count_of_queue_peeks[state],
                    "Unit": "Count",
                },
            ],
        )

    def run(self):
        try:
            self._run()
        except Exception as ex:
            _log.exception("exit: foqus_service unhandled exception")
            _publish_service_error(message=repr(ex), detail=traceback.format_exc())
            raise

    def _run(self):
        """main loop for running foqus
        Pop a job off FOQUS-JOB-QUEUE, call setup, then delete the job and call run.
        """
        _log.debug("main loop flowsheet service")
        try:
            self.increment_metric_queue_peeks(state="start", reset=True)
        except Exception as ex:
            _log.error("put metric queue peeks failed: %s", repr(ex))
            raise
        self._receipt_handle = None
        VisibilityTimeout = 60 * 10
        db = TurbineLiteDB()
        # getJobStatus._db  = db
        _log.debug("Consumer Register")
        db.consumer_register()
        db.add_message("Consumer Registered")
        self._kat = _KeepAliveTimer(db, freq=60)
        self._kat.start()
        dat = None
        while not self._stop:
            ret = None
            _log.debug("pop job")
            try:
                ret = self.pop_job(db, VisibilityTimeout=VisibilityTimeout)
            except FOQUSJobException as ex:
                job_desc = ex.job_desc
                _log.exception("verify foqus exception: %s", repr(ex))
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message(
                    "job failed in verify: %r" % (ex), job_desc["Id"], exception=msg
                )
                self._delete_sqs_job()
                self.increment_metric_job_finished(event="error.job.verify")
                continue
            except Exception as ex:
                _log.exception("pop_job exception: %s", repr(ex))
                raise

            if not ret:
                continue

            assert type(ret) is tuple and len(ret) == 2
            _log.debug("pop_job return:  %s", str(ret))
            user_name, job_desc = ret
            job_id = job_desc["Id"]
            session_id = job_desc["sessionid"]
            # if msg_attr_session_id != session_id:
            #     _log.error("run: session IDs mismatch MessageAttributes(%s) and Message(%s)",
            #         msg_attr_session_id, session_id)
            #     db.job_change_status(job_desc, "error", message=msg)
            #     db.add_message(
            #         "run: job.submit session IDs mismatch MessageAttributes(%s) and Message(%s)" %(
            #         msg_attr_session_id, session_id)
            #     )
            #     self._delete_sqs_job()
            #     self.increment_metric_job_finished(event="error.session.mismatch")
            #     continue
            # session_id = uuid.UUID(sessionid)

            """
            TODO: check dynamodb table if job has been stopped or killed
            cannot stop a running job.  If entry is missing job is ignored.
            """
            try:
                table = self._dynamodb.describe_table(
                    TableName=self._dynamodb_table_name
                )
            except botocore.exceptions.ClientError as ex:
                _log.exception(
                    "UserData Configuration Error No DynamoDB Table %s"
                    % self._dynamodb_table_name
                )
                raise

            response = self._dynamodb.get_item(
                TableName=self._dynamodb_table_name,
                Key={"Id": {"S": str(job_id)}, "Type": {"S": "Job"}},
            )

            item = response.get("Item")
            if not item:
                msg = "Job %s expired:  Not in DynamoDB table %s" % (
                    job_id,
                    self._dynamodb_table_name,
                )
                _log.info(msg)
                self._delete_sqs_job()
                db.job_change_status(job_desc, "expired", message=msg)
                db.add_message("Job has Expired", jobid=str(job_id))
                self.increment_metric_job_finished(event="expired.job")
                continue

            """ Job is Finished it is in state (terminate,stop,success,error)
            """
            if item.get("Finished", None):
                _log.info("Job %s will be dequeued and ignored", str(job_id))
                self._delete_sqs_job()
                db.add_message("Job State %s" % item["Finished"], jobid=str(job_id))
                self.increment_metric_job_finished(event="ignore.job.finished")
                continue
            try:
                dat = self.setup_foqus(db, user_name, job_desc)
            except NotImplementedError as ex:
                _log.exception("setup foqus NotImplementedError")
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message(
                    "job failed in setup NotImplementedError",
                    job_desc["Id"],
                    exception=msg,
                )
                self._delete_sqs_job()
                raise
            except foqusException as ex:
                # TODO:
                _log.exception("setup foqus exception: job fails, continue running")
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message(
                    "job failed in setup: %r" % (ex), job_desc["Id"], exception=msg
                )
                self.increment_metric_job_finished(event="error.job.setup")
                self._delete_sqs_job()
                continue
            except Exception as ex:
                # TODO:
                _log.exception("setup foqus exception:  fatal error")
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message(
                    "job failed in setup: %r" % (ex), job_desc["Id"], exception=msg
                )
                self.increment_metric_job_finished(event="error.job.setup")
                self._delete_sqs_job()
                raise

            _log.debug("BEFORE run_foqus")
            self._delete_sqs_job()
            try:
                self.run_foqus(db, job_desc)
            except Exception as ex:
                _log.exception("run_foqus Exception")
                self.increment_metric_job_finished(event="error.job.run")
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message(
                    "job failed in setup: %r" % (ex), job_desc["Id"], exception=msg
                )
                self.close()
                raise

        _log.debug("STOP CALLED")
        self.close()

    def close(self):
        dat = self._dat
        kat = self._kat
        if not dat:
            _log.debug("close: session dat is None")
            return
        if kat is not None:
            kat.terminate()
        try:
            dat.flowsheet.turbConfig.stopAllConsumers()
        except Exception as ex:
            _log.exception("reset stop all consumers")
            raise
        try:
            dat.flowsheet.turbConfig.closeTurbineLiteDB()
        except Exception as ex:
            _log.exception("reset close turbineLite")
            raise

    def _delete_sqs_job(self):
        """Delete the job after setup completes or there is an error."""
        _log.debug("DELETE received message from queue: %s", self._receipt_handle)
        self._sqs.delete_message(
            QueueUrl=self._queue_url, ReceiptHandle=self._receipt_handle
        )

    def _check_job_terminate(self, job_id):
        response = self._dynamodb.get_item(
            TableName=self._dynamodb_table_name,
            Key={"Id": {"S": str(job_id)}, "Type": {"S": "Job"}},
        )

        item = response.get("Item")
        if not item:
            _log.warn(
                "Job %s expired:  Not in DynamoDB table %s"
                % (job_id, self._dynamodb_table_name)
            )
            return

        """ Job is Finished it is in state (terminate,stop,success,error)
        """
        if item.get("Finished", None):
            state = item.get("State")
            _log.info("Job %s in Finished State=%s", str(job_id), state)
            return state == "terminate"
        return False

    def pop_job(self, db, VisibilityTimeout=300):
        """Pop job from AWS SQS, Download FOQUS Flowsheet from AWS S3

        SQS Job Body Contain Job description, for example:
        [{"Initialize":false,
        "Input":{},
        "Reset":false,
        "Simulation":"BFB_v11_FBS_01_26_2018",
        "Visible":false,
        "Id":"8a3033b4-6de2-409c-8552-904889929704"}]
        """
        # Receive message from SQS queue
        response = self._sqs.receive_message(
            QueueUrl=self._queue_url,
            AttributeNames=["SentTimestamp"],
            MaxNumberOfMessages=1,
            MessageAttributeNames=["All"],
            VisibilityTimeout=VisibilityTimeout,
            WaitTimeSeconds=10,
        )

        if not response.get("Messages", None):
            _log.info("Job Queue is Empty")
            self.increment_metric_queue_peeks(state="empty")
            return

        self.increment_metric_queue_peeks(state="start")
        message = response["Messages"][0]
        self._receipt_handle = message["ReceiptHandle"]
        body = message["Body"]
        message_attr = message.get("MessageAttributes")
        _log.info("RESPONSE: " + str(response))
        _log.info("MessageAttributes: " + str(message_attr))
        if message_attr is None:
            _log.error("Reject: Job has no MessageAttributes")
            self.increment_metric_job_finished(event="invalid.job")
            self._delete_sqs_job()
            return

        user_name = message_attr.get("username", {}).get("StringValue")
        _log.info("username: %s", user_name)
        session_id = message_attr.get("session", {}).get("StringValue")
        _log.info("session: %s", session_id)
        job_id = message_attr.get("job", {}).get("StringValue")
        _log.info("job: %s", job_id)
        if not job_id:
            _log.error("Reject Job:  job unspecified")
            self._delete_sqs_job()
            return
        if not session_id:
            _log.error("Reject Job(%s):  session unspecified", job_id)
            self._delete_sqs_job()
            return
        if not user_name:
            _log.error("Reject Job(%s):  user unspecified", job_id)
            self._delete_sqs_job()
            return

        try:
            uuid.UUID(job_id)
        except ValueError as err:
            _log.exception("job_id(%s) UUID ValueError", job_id)
            self._delete_sqs_job()
            return
        except TypeError as err:
            _log.exception("job_id(%s) UUID TypeError", job_id)
            self._delete_sqs_job()
            return

        try:
            uuid.UUID(session_id)
        except ValueError as err:
            _log.exception("session_id(%s) UUID ValueError", session_id)
            self._delete_sqs_job()
            return
        except TypeError as err:
            _log.exception("session_id(%s) UUID TypeError", session_id)
            self._delete_sqs_job()
            return

        d = dict(sessionid=session_id, Id=job_id)
        if not db.authorize_user_name(user_name):
            db.job_change_status(
                d, "error", message="Authorization Failed: wrong user(%s)" % (user_name)
            )
            self._delete_sqs_job()
            return

        try:
            job_desc = json.loads(body)
        except Exception as ex:
            _log.error("Reject Job: %s", repr(ex))
            db.job_change_status(d, "invalid", message=repr(ex))
            self._delete_sqs_job()
            return

        job_desc.update(d)
        job_input = job_desc.get("Input", [])
        simulation_name = job_desc.get("Simulation")
        if not simulation_name:
            _log.error("Reject:  Job description has no Simulation")
            d = dict(sessionid=session_id, Id=job_id)
            db.job_change_status(d, "invalid", message="no simulation specified")
            self._delete_sqs_job()
            return

        sfile, rfile, vfile, ofile = getfilenames(job_id)
        with open(vfile, "w") as fd:
            json.dump(dict(input=job_input), fd)

        bucket_name = FOQUSAWSConfig.get_instance().get_simulation_bucket_name()
        _log.info("Simulation Bucket: " + bucket_name)
        s3 = boto3.client("s3", region_name=FOQUSAWSConfig.get_instance().get_region())
        flowsheet_key = "%s/%s/session.foqus" % (user_name, simulation_name)
        l = s3.list_objects(
            Bucket=bucket_name, Prefix="%s/%s/" % (user_name, simulation_name)
        )
        # BFB_OUU_MultVar_04.09.2018.foqus
        if "Contents" not in l:
            _log.error(
                "S3 Simulation:  No keys match %s/%s" % (user_name, simulation_name)
            )
            raise FOQUSJobException(
                "S3 Bucket %s missing key username/simulation %s/%s"
                % (bucket_name, user_name, simulation_name),
                job_desc,
                user_name,
            )

        foqus_keys = [i["Key"] for i in l["Contents"] if i["Key"].endswith(".foqus")]
        if len(foqus_keys) < 1:
            _log.error(
                "S3 Simulation:  No keys match %s"
                % "%s/%s/*.foqus"
                % (user_name, simulation_name)
            )
            raise FOQUSJobException(
                "S3 Bucket No FOQUS File: %s/%s/%s/*.foqus"
                % (bucket_name, user_name, simulation_name),
                job_desc,
                user_name,
            )
        if len(foqus_keys) > 1:
            _log.error("S3 Simulations:  Multiple  %s" % str(foqus_keys))
            raise FOQUSJobException(
                "S3 Bucket Multiple FOQUS Files: %s/%s/%s/*.foqus"
                % (bucket_name, user_name, simulation_name),
                job_desc,
                user_name,
            )

        if flowsheet_key not in foqus_keys:
            _log.error("S3 Simulations:  Missing flowsheet key  %s" % str(foqus_keys))
            raise FOQUSJobException(
                "S3 Bucket Missing flowsheet key : %s/%s/%s/*.foqus"
                % (bucket_name, user_name, simulation_name),
                job_desc,
                user_name,
            )

        idx = foqus_keys.index(flowsheet_key)
        _log.info("S3: Download Key %s", flowsheet_key)
        s3.download_file(bucket_name, flowsheet_key, sfile)

        # WRITE CURRENT JOB TO FILE
        with open(os.path.join(CURRENT_JOB_DIR, "current_foqus.json"), "w") as fd:
            json.dump(job_desc, fd)

        return user_name, job_desc

    # @staticmethod
    def setup_foqus(self, db, user_name, job_desc):
        """
        Move job to state setup
        Pull FOQUS nodes' simulation files from AWS S3
        ACM simulations store in TurbineLite
        """
        sfile, rfile, vfile, ofile = getfilenames(job_desc["Id"])
        guid = job_desc["Id"]
        jid = None
        simulation_name = job_desc["Simulation"]
        # Run the job
        db.add_message("consumer={0}, setup foqus job".format(db.consumer_id), guid)
        _log.debug("setup foqus")
        db.job_change_status(job_desc, "setup")
        configContent = db.get_configuration_file(simulation_name)
        logging.getLogger("foqus." + __name__).info("Job {0} is submitted".format(guid))

        reset = job_desc.get("Reset", False)
        assert type(reset) is bool, "Bad type for reset %s" % type(reset)
        if self._dat != None:
            assert type(self._dat) is Session
        else:
            reset = True

        if self._simulation_name != simulation_name:
            reset = True

        dat = self._dat
        if reset == True:
            _log.debug("Reset Flowsheet")
            self.close()
            self._dat = dat = Session(useCurrentWorkingDir=True)
            _log.debug("New Session Created: next load")
            dat.load(sfile, stopConsumers=True)
            _log.debug("Session load finished")
            self._simulation_name = simulation_name
        else:
            _log.debug("No Reset Flowsheet")

        # Load next job inputs
        dat.loadFlowsheetValues(vfile)
        _log.debug("Process Flowsheet nodes")
        count_turb_apps = 0
        turb_app_nkey = None
        foqus_user_plugins = []
        for i in dat.flowsheet.nodes:
            node = dat.flowsheet.nodes[i]
            if node.turbApp is not None:
                turb_app = node.turbApp[0]
                turb_app = turb_app.lower()
                if turb_app == "foqus-user-plugin":
                    foqus_user_plugins.append(i)
                    continue
                turb_app_nkey = i
                count_turb_apps += 1

        user_plugin_dir = os.path.join(WORKING_DIRECTORY, "user_plugins")
        for i in foqus_user_plugins:
            _setup_foqus_user_plugin(
                dat, i, user_name=user_name, user_plugin_dir=user_plugin_dir
            )

        pymodels = pluginSearch.plugins(
            idString="#\s?FOQUS_PYMODEL_PLUGIN",
            pathList=[
                user_plugin_dir,
                os.path.dirname(pymodel.__file__),
            ],
        )
        dat.pymodels = pymodels
        dat.flowsheet.pymodels = pymodels
        # Check if Plugin Available
        for i in foqus_user_plugins:
            # node = dat.flowsheet.nodes[i]
            if i not in pymodels.plugins:
                for key in pymodels.plugins:
                    _log.debug("PLUGIN: %s" % (key))
                if i in pymodels.check_available_error_d:
                    msg = pymodels.check_available_error_d.get(i)
                    raise foqusException(
                        "FOQUS User Plugin %s:  Failed to load on check available: %s"
                        % (i, msg)
                    )
                raise foqusException("FOQUS User Plugin %s:  Failed to load" % (i))

        if count_turb_apps > 1:
            self.close()
            raise RuntimeError(
                "setup_foqus: Not supporting Flowsheet with multiple Turbine App nodes"
            )
        if count_turb_apps:
            try:
                _setup_flowsheet_turbine_node(dat, turb_app_nkey, user_name=user_name)
            except AssertionError as ex:
                _log.error("Job Setup Failure: %s", str(ex))
                db.job_change_status(
                    job_desc, "error", message="Error in job setup: %s" % ex
                )

        return dat

    def run_foqus(self, db, job_desc):
        """Run FOQUS Flowsheet in thread
        paramseters:
            db -- TurbineLiteDB instance
            dat.flowsheet -- foqus.framework.graph.graph
        """
        dat = self._dat
        assert isinstance(db, TurbineLiteDB)
        assert isinstance(dat, Session)
        assert isinstance(dat.flowsheet, Graph)
        exit_code = 0
        sfile, rfile, vfile, ofile = getfilenames(job_desc["Id"])
        guid = job_desc["Id"]
        jid = guid  # NOTE: like to use actual increment job id but hard to find.
        db.job_change_status(job_desc, "running")
        gt = dat.flowsheet.runAsThread()
        assert isinstance(gt, Graph)
        terminate = False
        while gt.is_alive():
            gt.join(10)
            status = db.consumer_status()
            if status == "terminate" or self._stop or self._check_job_terminate(jid):
                terminate = True
                db.job_change_status(
                    job_desc,
                    "error",
                    message="terminate flowsheet: status=%s stop=%s"
                    % (status, self._stop),
                )
                break

        if terminate:
            _log.debug("terminate job %s", jid)
            try:
                gt.terminate()
            except Exception as ex:
                msg = "terminating job %s exception %s" % (jid, str(ex))
                _log.debug(msg)
                db.add_message("job %s: terminated" % guid, guid)
            else:
                db.add_message("job %s: terminated" % guid, guid)
            self.increment_metric_job_finished(event="terminate.job")
            return

        if gt.res[0]:
            if type(gt.res[0]) is not dict:
                _log.error("Expecting job Output dictionary: %s", str(gt.res))
                raise foqusException("Run Flowsheet Bad Output: %s" % (str(gt.res)))

            # NOTE: Nodes need empty entries to pass loadValues
            # else get an exception
            if len(dat.flowsheet.input_vectorlist) == 0:
                for k in gt.res[0]["input_vectorvals"]:
                    dat.flowsheet.input_vectorlist.addNode(k)

            if len(dat.flowsheet.output_vectorlist) == 0:
                for k in gt.res[0]["input_vectorvals"]:
                    dat.flowsheet.output_vectorlist.addNode(k)

            try:
                dat.flowsheet.loadValues(gt.res[0])
            except NodeVarListEx as ex:
                db.job_change_status(job_desc, "error", message=ex.getCodeString())
                raise
        else:
            dat.flowsheet.errorStat = 19

        dat.saveFlowsheetValues(ofile)
        db.job_save_output(job_desc, CURRENT_JOB_DIR)
        dat.save(
            filename=rfile,
            updateCurrentFile=False,
            changeLogMsg="Saved Turbine Run",
            bkp=False,
            indent=0,
        )

        # NOTE: Attempt to allow output to
        #    reach DynamoDB table before triggering
        #    reading the final job result from
        #    DynamoDB to S3.
        #  Also should be handled by lambda retry
        #  if output not available yet, 500 error from FaaS
        #  occurs, and update function will be tried again.
        time.sleep(2)

        if dat.flowsheet.errorStat == 0:
            db.job_change_status(job_desc, "success")
            db.add_message(
                "consumer={0}, job {1} finished, success".format(db.consumer_id, jid),
                guid,
            )
            self.increment_metric_job_finished(event="success.job")
        else:
            msg = "Unknown"
            if gt.ex:
                exc_type, exc_value, exc_tb = gt.ex
                msg = traceback.format_exception(exc_type, exc_value, exc_tb)
            db.job_change_status(
                job_desc,
                "error",
                message="Flowsheet Error: %s" % (msg),
            )
            db.add_message(
                "consumer={0}, job {1} finished, error".format(db.consumer_id, jid),
                guid,
            )
            self.increment_metric_job_finished(
                event="error.flowsheet.%s" % (dat.flowsheet.errorStat)
            )

        _log.info("Job {0} finished".format(jid))
