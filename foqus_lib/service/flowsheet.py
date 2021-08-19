###############################################################################
# FOQUS Copyright (c) 2012 - 2021, by the software owners: Oak Ridge Institute
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
#
###############################################################################
"""foqus_service.py
* The AWS Cloud FOQUS service to start FOQUS

Joshua Boverhof, Lawrence Berkeley National Lab

"""
import socket
import os
import time
import boto3,optparse
import sys,json,signal,os,errno,uuid,threading,time,traceback
from os.path import expanduser
import urllib.request, urllib.error, urllib.parse
from foqus_lib.framework.session.session import session as Session
from foqus_lib.framework.session.session import generalSettings as FoqusSettings
from foqus_lib.framework.graph.graph import Graph
from turbine.commands import turbine_simulation_script
import logging
import logging.config
import botocore.exceptions

_instanceid = None
WORKING_DIRECTORY = os.path.abspath(os.environ.get('FOQUS_SERVICE_WORKING_DIR', "\\ProgramData\\foqus_service"))
AWS_REGION = 'us-east-1'
DEBUG = False
CURRENT_JOB_DIR = None
_log = None

def _set_working_dir(wdir):
    global _log, WORKING_DIRECTORY
    WORKING_DIRECTORY = wdir
    log_dir = os.path.join(wdir, "logs")
    try: os.makedirs(log_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    os.chdir(wdir)
    FoqusSettings().applyLogSettings()

    _log = logging.getLogger('foqus.foqus_lib.service.flowsheet')
    _log.setLevel(logging.DEBUG)
    _log.info('Working Directory: %s', WORKING_DIRECTORY)
    logging.getLogger('boto3').setLevel(logging.ERROR)
    logging.getLogger('botocore').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)


def _get_user_config_location(*args, **kw):
    _log.debug("USER CONFIG: %s", str(args))
    return os.path.join(WORKING_DIRECTORY, 'foqus.cfg')
FoqusSettings.getUserConfigLocation = _get_user_config_location


def getfilenames(jid):
    global CURRENT_JOB_DIR
    CURRENT_JOB_DIR = os.path.join(WORKING_DIRECTORY, str(jid))

    _log.info('Job Directory: %s', CURRENT_JOB_DIR)
    try: os.makedirs(CURRENT_JOB_DIR)
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
    return sfile,rfile,vfile,ofile


def scrub_empty_string_values_for_dynamo(db):
    """ DynamoDB throws expection if there is an empty string in dict
    ValidationException: ExpressionAttributeValues contains invalid value:
    One or more parameter values were invalid: An AttributeValue may not contain an empty string for key :o
    """
    if type(db) is not dict: return
    for k,v in list(db.items()):
        if v in  ("",""): db[k] = "NULL"
        else: scrub_empty_string_values_for_dynamo(v)


def _setup_flowsheet_turbine_node(dat, nkey, user_name):
    """ From s3 download all simulation files into AspenSinterComsumer cache directory '{working_directory\test\{simulation_guid}'.  If
    Simulation does not exist create one.  If Simulation does exist just s3 download all simulation files into the above cache directory.

    The new simulation_guid is created for all file updates to TurbineWS, so this is sidestepping that process.

    TODO: Provide a simulation_id via S3 ( eg.  {simulation_name}/Id )

    """
    assert len(dat.flowsheet.nodes[nkey].turbApp) == 2, \
        'DAT Flowsheet nodes turbApp is %s' %dat.flowsheet.nodes[nkey].turbApp

    node = dat.flowsheet.nodes[nkey]
    turb_app = node.turbApp[0]
    model_name = node.modelName
    assert turb_app is not None
    turb_app = turb_app.lower()
    assert turb_app in ['acm', 'aspenplus'], 'unknown turbine application "%s"' %turb_app

    """ Search S3 Bucket for node simulation
    """
    s3 = boto3.client('s3', region_name=AWS_REGION)
    bucket_name = FOQUSAWSConfig.get_instance().get_simulation_bucket_name()
    prefix = '%s/%s/' %(user_name,model_name)
    l = s3.list_objects(Bucket=bucket_name, Prefix=prefix)
    assert 'Contents' in l, 'Node %s failure: S3 Bucket %s is missing simulation files for "%s"' %(nkey, bucket_name, prefix)
    key_sinter_filename = None
    key_model_filename = None
    s3_key_list = [i['Key'] for i in l['Contents']]
    _log.debug('Node model %s staged-input files %s' %(model_name, s3_key_list))
    for k in s3_key_list:
        if k.endswith('/%s_sinter.json' %turb_app):
            key_sinter_filename = k
        elif turb_app == 'acm' and k.endswith('.acmf'):
            assert key_model_filename is None, 'detected multiple model files'
            key_model_filename = k
        elif turb_app == 'aspenplus' and k.endswith('.bkp'):
            assert key_model_filename is None, 'detected multiple model files'
            key_model_filename = k

    assert key_sinter_filename is not None, 'Flowsheet node=%s simulation=%s sinter configuration not in %s' %(nkey, model_name, str(s3_key_list))
    assert key_model_filename is not None, 'Flowsheet node=%s simulation=%s model file not in %s' %(nkey, model_name, str(s3_key_list))

    """ search TurbineLite WS for node simulation
    """
    print(turbine_simulation_script.__file__)
    turbine_cfg = node.gr.turbConfig.getFile()
    _log.debug('CWD: %s', os.path.abspath(os.path.curdir))
    turbine_cfg = os.path.abspath(turbine_cfg)
    _log.debug('Turbine Configuration File: %s', turbine_cfg)
    sim_list = turbine_simulation_script.main_list([turbine_cfg], func=None)
    print('Simulation List %s' %sim_list)
    sim_d = [i for i in sim_list if i['Name'] == model_name]
    cache_sim_guid = None
    assert len(sim_d) < 2, 'Expecting 0 or 1 entries for simulation %s' %model_name
    if len(sim_d) == 0:
        _log.debug('No simulation="%s" in TurbineLite' %model_name)
        sim_d = None
        cache_sim_guid = str(uuid.uuid4())
    else:
        _log.debug('Found simulation="%s" in TurbineLite' %model_name)
        sim_d = sim_d[0]
        assert 'Id' in sim_d, 'Missing keys in Simulation %s' %sim_d
        cache_sim_guid = sim_d['Id']

    """ upload all staged-inputs to TurbineLite if new or updated in
    s3://{bucketname}/{username}/{simulation}
    """
    entry_list = [i for i in l['Contents'] if i['Key'] != prefix and i['Key'].startswith(prefix)]
    update_required = False
    #target_dir = os.path.join(CURRENT_JOB_DIR, model_name)
    target_dir = os.path.join(WORKING_DIRECTORY, 'test', cache_sim_guid)
    os.makedirs(target_dir, exist_ok=True)
    sinter_local_filename = None
    for entry in entry_list:
        _log.debug("s3 staged input: %s", entry)
        key = entry['Key']
        etag = entry.get('ETag', "").strip('"')
        # Upload to TurbineLite
        # if ends with json or acmf
        si_metadata = []
        target_file_path = None
        assert key.startswith(prefix)
        if key == key_sinter_filename:
            #assert key_sinter_filename == '/'.join(prefix, key_sinter_filename.split('/')[-1]), \
            #    'sinter configuration "%s" must be in model base directory: "%s"' %(key_model_filename,prefix)
            target_file_path = os.path.join(target_dir, "sinter_configuration.txt")
            sinter_local_filename = target_file_path
            if sim_d: si_metadata = [i for i in sim_d["StagedInputs"] if i['Name'] == 'configuration']
            s3.download_file(bucket_name, key, target_file_path)
        elif key == key_model_filename:
            #assert key_model_filename == '/'.join(prefix, key_model_filename.split('/')[-1]), \
            #    'sinter configuration "%s" must be in model base directory: "%s"' %(key_model_filename,prefix)
            target_file_path = os.path.join(target_dir, key.split('/')[-1])
            if sim_d: si_metadata = [i for i in sim_d["StagedInputs"] if i['Name'] == 'aspenfile']
            s3.download_file(bucket_name, key, target_file_path)
        else:
            args = [ i for i in key[len(prefix):].split('/') if i ]
            args.insert(0, target_dir)
            target_file_path = os.path.join(*args)
            if sim_d: si_metadata = [i for i in sim_d["StagedInputs"] if i['Name'] == key.split('/')[-1]]
            s3.download_file(bucket_name, key, target_file_path)

        _log.debug('model="%s" key="%s" staged-in file="%s"' %(model_name, key, target_file_path))
        assert len(si_metadata) < 2, 'Turbine Error:  Duplicate entries for "%s", "%s"' %(model_name, key)
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


    assert sinter_local_filename is not None, 'missing sinter configuration file'

    if sim_d is None:
        _log.debug('Adding Simulation "%s" "%s"' %(model_name,cache_sim_guid))
        node.gr.turbConfig.uploadSimulation(model_name, sinter_local_filename, guid=cache_sim_guid, update=False)
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
    """ Custom Exception for holding onto the job description and user name """
    def __init__(self, message, job_desc, user_name):
        super().__init__(message)
        self.job_desc = job_desc
        self.user_name = user_name


class FOQUSAWSConfig:
    """
    {"FOQUS-Update-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Update-Topic",
     "FOQUS-Message-Topic-Arn":"arn:aws:sns:us-east-1:387057575688:FOQUS-Message-Topic",
     "FOQUS-Job-Queue-Url":"https://sqs.us-east-1.amazonaws.com/387057575688/FOQUS-Gateway-FOQUSJobSubmitQueue-XPNWLF4Q38FD",
     "FOQUS-Simulation-Bucket-Name":"foqussimulationdevelopment1562016460"
    }
    """
    _inst = None
    @classmethod
    def get_instance(cls):
        if cls._inst is not None: return cls._inst
        request = urllib.request.urlopen('http://169.254.169.254/latest/user-data')
        cls._inst = cls()
        cls._inst._d = json.load(request)
        return cls._inst
    def __init__(self):
        self._d = None
    def _get(self, key):
        v = self._d.get(key)
        assert v, "UserData Missing Key: %s" %key
        _log.debug('FOQUSAWSConfig._get: %s = %s' %(key,v))
        return v
    def get_update_topic_arn(self):
        return self._get("FOQUS-Update-Topic-Arn")
    def get_message_topic_arn(self):
        return self._get("FOQUS-Message-Topic-Arn")
    def get_job_queue_url(self):
        return self._get("FOQUS-Job-Queue-Url")
    def get_simulation_bucket_name(self):
        return self._get("FOQUS-Simulation-Bucket-Name")
    def get_dynamo_table_name(self):
        return self._get("FOQUS-DynamoDB-Table")


class _KeepAliveTimer(threading.Thread):
    def __init__(self, turbineDB, freq=60):
        threading.Thread.__init__(self)
        self.stop = threading.Event() # flag to stop thread
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
    """
    """
    def __init__(self, close_after=True):
        self._sns = boto3.client('sns', region_name=AWS_REGION)
        self._topic_arn = FOQUSAWSConfig.get_instance().get_update_topic_arn()
        self._topic_msg_arn = FOQUSAWSConfig.get_instance().get_message_topic_arn()
        self._user_name = 'unknown'
        self.consumer_id = str(uuid.uuid4())

    def _sns_notification(self, obj):
        _log.debug('_sns_notification obj: %s' %obj)
        resource = obj.get('resource', 'unknown')
        status = obj.get('status', 'unknown')
        if resource == 'consumer':
            status = obj.get('event', 'unknown')
        event = '%s.%s' %(resource,status)
        _log.debug('_sns_notification event: %s' %event)
        attrs = dict(event=dict(DataType='String', StringValue=event),
                     username=dict(DataType='String', StringValue=self._user_name))
        _log.debug('MessageAttributes: %s' %attrs)
        self._sns.publish(Message=json.dumps([obj]),
                          MessageAttributes=attrs,
                          TopicArn=self._topic_arn)

    def __del__(self):
        _log.info("%s.delete", self.__class__.__name__)
    def set_user_name(self, name):
        self._user_name = name
    def connectionString(self):
        _log.info("%s.connectionString", self.__class__.__name__)
    def getConnection(self, rc=0):
        _log.info("%s.getConnection", self.__class__.__name__)
    def closeConnection(self):
        _log.info("%s.closeConnection", self.__class__.__name__)
    def add_new_application(self, applicationName, rc=0):
        _log.info("%s.add_new_application", self.__class__.__name__)
    def add_message(self, msg, jobid="", **kw):
        d = dict(job=jobid, message=msg, consumer=self.consumer_id, instanceid=_instanceid, resource="job")
        d.update(kw)
        obj = json.dumps(d)
        _log.debug("%s.add_message: %s", self.__class__.__name__, obj)
        self._sns.publish(Message=obj, TopicArn=self._topic_msg_arn)

    def consumer_keepalive(self, rc=0):
        _log.info("%s.consumer_keepalive", self.__class__.__name__)
        self._sns_notification(dict(resource='consumer', event='running', rc=rc,
            consumer=self.consumer_id, instanceid=_instanceid))

    def consumer_status(self):
        _log.info("%s.consumer_status", self.__class__.__name__)
        #assert status in ['up','down','terminate'], ''
        #self._sns_notification(dict(resource='consumer', event=status, rc=rc, consumer=self.consumer_id))
        return 'up'
    def consumer_id(self, pid, rc=0):  # TODO pylint: disable=method-hidden
        _log.info("%s.consumer_id", self.__class__.__name__)
    def consumer_register(self, rc=0):
        _log.info("%s.consumer_register", self.__class__.__name__)
        d = dict(resource='consumer', instanceid=_instanceid, event='running', rc=rc, consumer=self.consumer_id)
        self._sns_notification(d)
        _log.info("%s.consumer_register: %s", self.__class__.__name__, str(d))
    #def get_job_id(self, simName=None, sessionID=None, consumerID=None, state='submit', rc=0):
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
        assert status in ['success', 'setup', 'running', 'error', 'terminate', 'expired'], \
            "Incorrect Job Status %s" %status
        _log.info("%s.job_change_status %s", self.__class__.__name__, job_d)
        d = dict(resource='job', event='status',
            rc=rc, status=status, jobid=job_d['Id'], instanceid=_instanceid,
            consumer=self.consumer_id,
            sessionid=job_d.get('sessionid','unknown'))
        if message: d['message'] = message
        self._sns_notification(d)

    def job_save_output(self, job_d, workingDir, rc=0):
        """ Save simulation output.  This is published to SNS, need to wait
        for tables to update before changing status to "success" or "error"
        otherwise "output" is occasionally not available yet.
        """
        assert type(job_d) is dict
        _log.info("%s.job_save_output", self.__class__.__name__)
        with open(os.path.join(workingDir, "output.json")) as outfile:
            output = json.load(outfile)
        scrub_empty_string_values_for_dynamo(output)
        _log.debug("%s.job_save_output:  %s", self.__class__.__name__, json.dumps(output))
        self._sns_notification(dict(resource='job',
            event='output', jobid=job_d['Id'], username=self._user_name, value=output, rc=rc,
            sessionid=job_d.get('sessionid','unknown')))


class FlowsheetControl:
    """ API for controlling Flowsheet process
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
        self._set_working_directory()
        socket.setdefaulttimeout(60)
        self._dat = None
        self._kat = None
        self._stop = False
        self._receipt_handle = None
        self._simulation_name = None
        self._sqs = boto3.client('sqs', region_name=AWS_REGION)
        self._queue_url = FOQUSAWSConfig.get_instance().get_job_queue_url()
        self._dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
        self._dynamodb_table_name = FOQUSAWSConfig.get_instance().get_dynamo_table_name()

    @classmethod
    def _set_working_directory(cls, working_dir=WORKING_DIRECTORY):
        if cls._is_set_working_directory:
            return
        _set_working_dir(working_dir)
        cls._is_set_working_directory = True

    def stop(self):
        self._stop = True

    def run(self):
        """ main loop for running foqus
        Pop a job off FOQUS-JOB-QUEUE, call setup, then delete the job and call run.
        """
        global _instanceid
        _log.debug("main loop flowsheet service")
        self._receipt_handle= None
        VisibilityTimeout = 60*10
        try:
            _instanceid = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read()
            _instanceid = _instanceid.decode('ascii')
        except:
            _log.error("Failed to discover instance-id")

        db = TurbineLiteDB()
        #getJobStatus._db  = db
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
                _log.exception("verify foqus exception: %s", str(ex))
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message("job failed in verify: %r" %(ex), job_desc['Id'], exception=msg)
                self._delete_sqs_job()
                continue
            except Exception as ex:
                _log.exception("pop_job exception: %s", str(ex))
                raise

            if not ret: continue
            assert type(ret) is tuple and len(ret) == 2
            user_name,job_desc = ret
            job_id = uuid.UUID(job_desc.get('Id'))
            #getJobStatus._flowsheet_job_id = str(job_id)
            db.set_user_name(user_name)
            """
            TODO: check dynamodb table if job has been stopped or killed
            cannot stop a running job.  If entry is missing job is ignored.
            """
            try:
                table = self._dynamodb.describe_table(TableName=self._dynamodb_table_name)
            except botocore.exceptions.ClientError as ex:
                _log.exception("UserData Configuration Error No DynamoDB Table %s" %self._dynamodb_table_name)
                raise

            response = self._dynamodb.get_item(
                       TableName=self._dynamodb_table_name,
                       Key={'Id':{'S':str(job_id)}, 'Type':{'S':'Job'}})

            item = response.get('Item')
            if not item:
                msg = "Job %s expired:  Not in DynamoDB table %s" %(job_id, self._dynamodb_table_name)
                _log.info(msg)
                self._delete_sqs_job()
                db.job_change_status(job_desc, "expired", message=msg)
                db.add_message("Job has Expired", jobid=str(job_id))
                continue

            """ Job is Finished it is in state (terminate,stop,success,error)
            """
            if item.get('Finished',None):
                _log.info("Job %s will be dequeued and ignored", str(job_id))
                self._delete_sqs_job()
                db.add_message("Job State %s" %item['Finished'], jobid=str(job_id))
                continue
            try:
                dat = self.setup_foqus(db, user_name, job_desc)
            except NotImplementedError as ex:
                _log.exception("setup foqus NotImplementedError: %s", str(ex))
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message("job failed in setup NotImplementedError", job_desc['Id'], exception=msg)
                self._delete_sqs_job()
                raise
                _log.exception("setup foqus URLError: %s", str(ex))
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message("job failed in setup URLError", job_desc['Id'], exception=msg)
                self._delete_sqs_job()
                raise
            except Exception as ex:
                # TODO:
                _log.exception("setup foqus exception: %s", str(ex))
                msg = traceback.format_exc()
                db.job_change_status(job_desc, "error", message=msg)
                db.add_message("job failed in setup: %r" %(ex), job_desc['Id'], exception=msg)
                self._delete_sqs_job()
                raise

            _log.debug("BEFORE run_foqus")
            self._delete_sqs_job()
            try:
                self.run_foqus(db, job_desc)
            except Exception as ex:
                _log.exception("run_foqus: %s", str(ex))
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
            _log.exception("reset stop all consumers: %s", str(ex))
            raise
        try:
            dat.flowsheet.turbConfig.closeTurbineLiteDB()
        except Exception as ex:
            _log.exception("reset close turbineLite DB %s", str(ex))
            raise

    def _delete_sqs_job(self):
        """ Delete the job after setup completes or there is an error.
        """
        _log.debug("DELETE received message from queue: %s", self._receipt_handle)
        self._sqs.delete_message(
            QueueUrl=self._queue_url,
            ReceiptHandle=self._receipt_handle
        )

    def _check_job_terminate(self, job_id):
        response = self._dynamodb.get_item(
                   TableName=self._dynamodb_table_name,
                   Key={'Id':{'S':str(job_id)}, 'Type':{'S':'Job'}})

        item = response.get('Item')
        if not item:
            _log.warn("Job %s expired:  Not in DynamoDB table %s" %(job_id, self._dynamodb_table_name))
            return

        """ Job is Finished it is in state (terminate,stop,success,error)
        """
        if item.get('Finished',None):
            state = item.get('State')
            _log.info("Job %s in Finished State=%s", str(job_id), state)
            return state == 'terminate'
        return False

    def pop_job(self, db, VisibilityTimeout=300):
        """ Pop job from AWS SQS, Download FOQUS Flowsheet from AWS S3

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
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=VisibilityTimeout,
            WaitTimeSeconds=10
        )
        if not response.get("Messages", None):
            _log.info("Job Queue is Empty")
            return

        message = response['Messages'][0]
        self._receipt_handle = message['ReceiptHandle']
        body = json.loads(message['Body'])
        _log.info('MessageAttributes: ' + str(body.get('MessageAttributes')))
        user_name = body['MessageAttributes'].get('username').get('Value')
        _log.info('username: ' + user_name)
        db.set_user_name(user_name)
        job_desc = json.loads(body['Message'])
        _log.info('Job Description: ' + body['Message'])
        for key in ['Id', 'Input', 'Simulation']:
            if job_desc.get(key) is None:
                raise FOQUSJobException("Job Description Missing Key %s" %key, job_desc, user_name)

        sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
        with open(vfile,'w') as fd:
            json.dump(dict(input=job_desc['Input']), fd)

        bucket_name = FOQUSAWSConfig.get_instance().get_simulation_bucket_name()
        _log.info('Simulation Bucket: ' + bucket_name)
        s3 = boto3.client('s3', region_name=AWS_REGION)
        simulation_name = job_desc['Simulation']
        flowsheet_key = '%s/%s/session.foqus' %(user_name, simulation_name)

        l = s3.list_objects(Bucket=bucket_name, Prefix='%s/%s/' %(user_name, simulation_name))
        # BFB_OUU_MultVar_04.09.2018.foqus
        if 'Contents' not in l:
            _log.error("S3 Simulation:  No keys match %s/%s" %(user_name, simulation_name))
            raise FOQUSJobException("S3 Bucket %s missing key username/simulation %s/%s" %(bucket_name,
                user_name, simulation_name), job_desc, user_name)

        foqus_keys = [i['Key'] for i in l['Contents'] if i['Key'].endswith('.foqus')]
        if len(foqus_keys) < 1:
            _log.error("S3 Simulation:  No keys match %s" %'%s/%s/*.foqus' %(user_name,simulation_name))
            raise FOQUSJobException("S3 Bucket No FOQUS File: %s/%s/%s/*.foqus" %(bucket_name,
                user_name, simulation_name), job_desc, user_name)
        if len(foqus_keys) > 1:
            _log.error("S3 Simulations:  Multiple  %s" %str(foqus_keys))
            raise FOQUSJobException("S3 Bucket Multiple FOQUS Files: %s/%s/%s/*.foqus" %(bucket_name,
                user_name, simulation_name), job_desc, user_name)

        if flowsheet_key not in foqus_keys:
            _log.error("S3 Simulations:  Missing flowsheet key  %s" %str(foqus_keys))
            raise FOQUSJobException("S3 Bucket Missing flowsheet key : %s/%s/%s/*.foqus" %(bucket_name,
                user_name, simulation_name), job_desc, user_name)

        #if '%s/%s/%s.foqus' %(user_name, simulation_name, simulation_name) not in foqus_keys:
        #    _log.error("S3 Simulations:  Multiple  %s" %str(foqus_keys))
        #    raise FOQUSJobException("S3 Bucket Multiple FOQUS Files: %s/%s/%s/*.foqus" %(bucket_name,
        #        user_name, simulation_name), job_desc, user_name)

        idx = foqus_keys.index(flowsheet_key)
        _log.info("S3: Download Key %s", flowsheet_key)
        s3.download_file(bucket_name, flowsheet_key, sfile)

        # WRITE CURRENT JOB TO FILE
        with open(os.path.join(CURRENT_JOB_DIR, 'current_foqus.json'), 'w') as fd:
            json.dump(job_desc, fd)

        return user_name,job_desc

    #@staticmethod
    def setup_foqus(self, db, user_name, job_desc):
        """
        Move job to state setup
        Pull FOQUS nodes' simulation files from AWS S3
        ACM simulations store in TurbineLite
        """
        sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
        guid = job_desc['Id']
        jid = None
        simulation_name = job_desc['Simulation']
        # Run the job
        db.add_message("consumer={0}, setup foqus job"\
            .format(db.consumer_id), guid)
        _log.debug("setup foqus")
        db.job_change_status(job_desc, "setup")
        configContent = db.get_configuration_file(simulation_name)
        logging.getLogger("foqus." + __name__)\
            .info("Job {0} is submitted".format(jid))

        reset = job_desc.get('Reset', False)
        assert type(reset) is bool, 'Bad type for reset %s' % type(reset)
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
            dat.load(sfile, stopConsumers=True)
            self._simulation_name = simulation_name
        else:
            _log.debug("No Reset Flowsheet")

        # Load next job inputs
        dat.loadFlowsheetValues(vfile)
        _log.debug("Process Flowsheet nodes")
        count_turb_apps = 0
        nkey = None
        for i in dat.flowsheet.nodes:
            if dat.flowsheet.nodes[i].turbApp is not None:
                nkey = i
                count_turb_apps += 1
        if count_turb_apps > 1:
            self.close()
            raise RuntimeError('setup_foqus: Not supporting Flowsheet with multiple Turbine App nodes')
        if count_turb_apps:
            try:
                _setup_flowsheet_turbine_node(dat, nkey, user_name=user_name)
            except AssertionError as ex:
                _log.error("Job Setup Failure: %s", str(ex))
                db.job_change_status(job_desc, "error",
                    message="Error in job setup: %s" %ex)
        return dat

    def run_foqus(self, db, job_desc):
        """ Run FOQUS Flowsheet in thread
        paramseters:
            db -- TurbineLiteDB instance
            dat.flowsheet -- foqus.framework.graph.graph
        """
        dat = self._dat
        assert isinstance(db, TurbineLiteDB)
        assert isinstance(dat, Session)
        exit_code = 0
        sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
        guid = job_desc['Id']
        jid = guid # NOTE: like to use actual increment job id but hard to find.
        db.job_change_status(job_desc, "running")
        gt = dat.flowsheet.runAsThread()
        assert isinstance(gt, Graph)
        terminate = False
        while gt.isAlive():
            gt.join(10)
            status = db.consumer_status()
            if status == 'terminate' or self._stop or self._check_job_terminate(jid):
                terminate = True
                db.job_change_status(job_desc, "error", message="terminate flowsheet: status=%s stop=%s" %(status, self._stop))
                #gt.terminate()
                break

        if terminate:
            _log.debug("terminate job %s", jid)
            try:
                gt.terminate()
            except Exception as ex:
                msg = "terminating job %s exception %s" %(jid,str(ex))
                _log.debug(msg)
                db.add_message("job %s: terminated" %guid, guid)
            else:
                db.add_message("job %s: terminated" %guid, guid)
            return

        if gt.res[0]:
            dat.flowsheet.loadValues(gt.res[0])
        else:
            dat.flowsheet.errorStat = 19

        dat.saveFlowsheetValues(ofile)
        db.job_save_output(job_desc, CURRENT_JOB_DIR)
        dat.save(
            filename = rfile,
            updateCurrentFile = False,
            changeLogMsg = "Saved Turbine Run",
            bkp = False,
            indent = 0)

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
                "consumer={0}, job {1} finished, success"\
                    .format(db.consumer_id, jid), guid)
        else:
            db.job_change_status(job_desc, "error",
                message="Flowsheet errorStat: %s" %dat.flowsheet.errorStat)
            db.add_message(
                "consumer={0}, job {1} finished, error"\
                    .format(db.consumer_id, jid), guid)

        _log.info("Job {0} finished".format(jid))
