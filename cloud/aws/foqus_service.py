"""foqus_service.py
* The AWS Cloud FOQUS service to start FOQUS

Joshua Boverhof, Lawrence Berkeley National Lab

See LICENSE.md for license and copyright details.
"""
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
import boto3,optparse
import sys,json,signal,os,errno,uuid,threading,time,traceback
from os.path import expanduser
import urllib.request, urllib.error, urllib.parse
from foqus_lib.framework.session.session import session as Session
from turbine.commands import turbine_simulation_script
import logging
import logging.config

_instanceid = None
WORKING_DIRECTORY = os.path.join("\\ProgramData\\foqus_service")

DEBUG = False
CURRENT_JOB_DIR = None
#try: os.makedirs(WORKING_DIRECTORY)
#except OSError as e:
#    if e.errno != errno.EEXIST: raise
#logging.basicConfig(filename="C:\\Users\\Administrator\\FOQUS-Cloud-Service.log",level=logging.DEBUG)
_log = None
"""
$($env:path);C:\ProgramData\Anaconda3\python27.zip;
C:\ProgramData\Anaconda3\lib\plat-win;
C:\ProgramData\Anaconda3\lib\lib-tk;
C:\ProgramData\Anaconda3\Library\bin;C:\ProgramData\Anaconda3\DLLs;C:\ProgramData\Anaconda2\lib;C:\ProgramData\Anaconda3;C:\ProgramData\Anaconda3\lib\site-packages;C:\ProgramData\Anaconda3\lib\site-packages\win32;C:\ProgramData\Anaconda3\lib\site-packages\win32\lib;C:\ProgramData\Anaconda3\lib\site-packages\Pythonwin
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
        cls.inst = cls()
        cls.inst._d = json.load(request)
        return cls.inst
    def get_update_topic_arn(self):
        return self._d.get("FOQUS-Update-Topic-Arn")
    def get_message_topic_arn(self):
        return self._d.get("FOQUS-Message-Topic-Arn")
    def get_job_queue_url(self):
        return self._d.get("FOQUS-Job-Queue-Url")
    def get_simulation_bucket_name(self):
        return self._d.get("FOQUS-Simulation-Bucket-Name")

def _set_working_dir():
    global _log
    log_dir = os.path.join(WORKING_DIRECTORY, "logs")
    try: os.makedirs(log_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    os.chdir(WORKING_DIRECTORY)
    logging.basicConfig(filename=os.path.join(log_dir, 'FOQUS-Cloud-Service.log'),level=logging.DEBUG)
    _log = logging.getLogger('foqus_service')
    _log.info('Working Directory: %s', WORKING_DIRECTORY)

    logging.getLogger('boto3').setLevel(logging.ERROR)
    logging.getLogger('botocore').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
_set_working_dir()
_log.debug('Loading')


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


class TurbineLiteDB:
    """
    """
    def __init__(self, close_after=True):
        self._sns = boto3.client('sns', region_name='us-east-1')
        topic = self._sns.create_topic(Name='FOQUS-Update-Topic')
        topic_messages = self._sns.create_topic(Name='FOQUS-Message-Topic')
        self._topic_arn = topic['TopicArn']
        self._topic_msg_arn = topic_messages['TopicArn']
        self.consumer_id = str(uuid.uuid4())

    def _sns_notification(self, obj):
        self._sns.publish(Message=json.dumps([obj]), TopicArn=self._topic_arn)

    def __del__(self):
        _log.info("%s.delete", self.__class__)
    def connectionString(self):
        _log.info("%s.connectionString", self.__class__)
    def getConnection(self, rc=0):
        _log.info("%s.getConnection", self.__class__)
    def closeConnection(self):
        _log.info("%s.closeConnection", self.__class__)
    def add_new_application(self, applicationName, rc=0):
        _log.info("%s.add_new_application", self.__class__)
    def add_message(self, msg, jobid, **kw):
        d = dict(job=jobid, message=msg, consumer=self.consumer_id, instanceid=_instanceid, resource="job")
        d.update(kw)
        obj = json.dumps(d)
        _log.debug("%s.add_message: %s", self.__class__, obj)
        self._sns.publish(Message=obj, TopicArn=self._topic_msg_arn)

    def consumer_keepalive(self, rc=0):
        _log.info("%s.consumer_keepalive", self.__class__)
        self._sns_notification(dict(resource='consumer', event='running', rc=rc,
            consumer=self.consumer_id, instanceid=_instanceid))

    def consumer_status(self):
        _log.info("%s.consumer_status", self.__class__)
        #assert status in ['up','down','terminate'], ''
        #self._sns_notification(dict(resource='consumer', event=status, rc=rc, consumer=self.consumer_id))
        return 'up'
    def consumer_id(self, pid, rc=0):
        _log.info("%s.consumer_id", self.__class__)
    def consumer_register(self, rc=0):
        _log.info("%s.consumer_register", self.__class__)
        d = dict(resource='consumer', instanceid=_instanceid, event='running', rc=rc, consumer=self.consumer_id)
        _log.info("%s.consumer_register: %s", self.__class__, str(d))
        self._sns_notification(d)
    def get_job_id(self, simName=None, sessionID=None, consumerID=None, state='submit', rc=0):
        _log.info("%s.get_job_id", self.__class__)
        return guid, jid, simId, reset

    def jobConsumerID(self, jid, cid=None, rc=0):
        _log.info("%s.jobConsumerID", self.__class__)
    def get_configuration_file(self, simulationId, rc=0):
        _log.info("%s.get_configuration_file", self.__class__)
    def job_prepare(self, jobGuid, jobId, configFile, rc=0):
        _log.info("%s.job_prepare", self.__class__)
    def job_change_status(self, jobGuid, status, rc=0):
        _log.info("%s.job_change_status %s", self.__class__, status)
        self._sns_notification(dict(resource='job', event='status',
            rc=rc, status=status, jobid=jobGuid, instanceid=_instanceid, consumer=self.consumer_id))
    def job_save_output(self, jobGuid, workingDir, rc=0):
        _log.info("%s.job_save_output", self.__class__)
        with open(os.path.join(workingDir, "output.json")) as outfile:
            output = json.load(outfile)
        scrub_empty_string_values_for_dynamo(output)
        _log.debug("%s.job_save_output:  %s", self.__class__, json.dumps(output))
        self._sns_notification(dict(resource='job',
            event='output', jobid=jobGuid, value=output, rc=rc))

def scrub_empty_string_values_for_dynamo(db):
    """ DynamoDB throws expection if there is an empty string in dict
    ValidationException: ExpressionAttributeValues contains invalid value:
    One or more parameter values were invalid: An AttributeValue may not contain an empty string for key :o
    """
    if type(db) is not dict: return
    for k,v in list(db.items()):
        if v in  ("",""): db[k] = "NULL"
        else: scrub_empty_string_values_for_dynamo(v)

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

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "FOQUS-Cloud-Service"
    _svc_display_name_ = "FOQUS Cloud Service"

    def __init__(self,args):
        _log.debug('AppServerSvc init')
        win32serviceutil.ServiceFramework.__init__(self,args)
        _log.debug('AppServerSvc init2')
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        _log.debug('AppServerSvc init3')
        socket.setdefaulttimeout(60)
        _log.debug('AppServerSvc init4')
        self._stop = False
        self._receipt_handle = None
        _log.debug('AppServerSvc init5')
        self._sqs = boto3.client('sqs', region_name='us-east-1')
        self._queue_url = FOQUSAWSConfig.get_instance().get_job_queue_url()
        _log.debug('AppServerSvc init finished')

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        _log.debug("stop called")
        self._stop = True

    def SvcDoRun(self):
        """ Pop a job off FOQUS-JOB-QUEUE, call setup, then delete the job and call run.
        """
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))

        global _instanceid
        _log.debug("starting")
        self._receipt_handle= None
        VisibilityTimeout = 60*10
        try:
            _instanceid = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read()
            _instanceid = _instanceid.decode('ascii')
        except:
            _log.error("Failed to discover instance-id")

        db = TurbineLiteDB()
        db.consumer_register()
        kat = _KeepAliveTimer(db, freq=60)
        kat.start()
        while not self._stop:
            ret = None
            try:
                ret = self.pop_job(VisibilityTimeout=VisibilityTimeout)
            except FOQUSJobException as ex:
                job_desc = ex.job_desc
                _log.exception("verify foqus exception: %s", str(ex))
                db.job_change_status(job_desc['Id'], "error")
                db.add_message("job failed in verify: %r" %(ex), job_desc['Id'], exception=traceback.format_exc())
                self._delete_sqs_job()
                continue

            if not ret: continue
            assert type(ret) is tuple and len(ret) == 2
            user_name,job_desc = ret
            try:
                dat = self.setup_foqus(db, user_name, job_desc)
            except NotImplementedError as ex:
                _log.exception("setup foqus NotImplementedError: %s", str(ex))
                db.job_change_status(job_desc['Id'], "error")
                db.add_message("job failed in setup NotImplementedError", job_desc['Id'], exception=traceback.format_exc())
                self._delete_sqs_job()
                raise
            except urllib.error.URLError as ex:
                _log.exception("setup foqus URLError: %s", str(ex))
                db.job_change_status(job_desc['Id'], "error")
                db.add_message("job failed in setup URLError", job_desc['Id'], exception=traceback.format_exc())
                self._delete_sqs_job()
                raise
            except Exception as ex:
                _log.exception("setup foqus exception: %s", str(ex))
                db.job_change_status(job_desc['Id'], "error")
                db.add_message("job failed in setup: %r" %(ex), job_desc['Id'], exception=traceback.format_exc())
                self._delete_sqs_job()
                raise
            else:
                _log.debug("BEFORE run_foqus")
                self._delete_sqs_job()
                self.run_foqus(db, dat, job_desc)

        _log.debug("STOP CALLED")

    def _delete_sqs_job(self):
        """ Delete the job after setup completes or there is an error.
        """
        _log.debug("DELETE received message from queue: %s", self._receipt_handle)
        self._sqs.delete_message(
            QueueUrl=self._queue_url,
            ReceiptHandle=self._receipt_handle
        )

    def pop_job(self, VisibilityTimeout=300):
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
        job_desc = json.loads(body['Message'])
        _log.info('Job Description: ' + body['Message'])
        for key in ['MessageAttributes', 'Id', 'Input']:
            if not job_desc.has_key(key):
                raise FOQUSJobException("Job Description Missing Key %s" %key)

        _log.info('MessageAttributes: ' + str(body.get('MessageAttributes')))
        user_name = body['MessageAttributes'].get('username').get('Value')
        _log.info('username: ' + user_name)
        sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
        with open(vfile,'w') as fd:
            json.dump(dict(input=job_desc['Input']), fd)

        bucket_name = FOQUSAWSConfig.get_instance().get_simulation_bucket_name()
        _log.info('Simulation Bucket: ' + bucket_name)
        s3 = boto3.client('s3', region_name='us-east-1')
        l = s3.list_objects(Bucket=bucket_name, Prefix='%s/%s' %(user_name, job_desc['Simulation']))
        # BFB_OUU_MultVar_04.09.2018.foqus
        if 'Contents' not in l:
            _log.error("S3 Simulation:  No keys match %s/%s" %(user_name, job_desc['Simulation']))
            raise FOQUSJobException("S3 Bucket %s missing key username/simulation %s/%s" %(bucket_name, user_name, job_desc['Simulation']),
                                   job_desc, user_name)

        foqus_keys = [i for i in l['Contents'] if i['Key'].endswith('.foqus')]
        if len(foqus_keys) == 0:
            _log.error("S3 Simulation:  No keys match %s" %'%s/%s/*.foqus' %(user_name,job_desc['Simulation']))
            raise FOQUSJobException("S3 Bucket No FOQUS File: %s/%s/%s/*.foqus" %(bucket_name, user_name, job_desc['Simulation']),
                                   job_desc, user_name)

        if len(foqus_keys) > 1:
            _log.error("S3 Simulations:  Multiple  %s" %str(foqus_keys))
            raise FOQUSJobException("S3 Bucket Multiple FOQUS Files: %s/%s/%s/*.foqus" %(bucket_name, user_name, job_desc['Simulation']),
                                   job_desc, user_name)

        _log.info("S3: Download Key %s", foqus_keys[0])
        s3.download_file(bucket_name, foqus_keys[0]['Key'], sfile)

        # WRITE CURRENT JOB TO FILE
        with open(os.path.join(CURRENT_JOB_DIR, 'current_foqus.json'), 'w') as fd:
            json.dump(job_desc, fd)

        return user_name,job_desc


    def setup_foqus(self, db, user_name, job_desc):
        """
        Move job to state setup
        Pull FOQUS nodes' simulation files from AWS S3
        ACM simulations store in TurbineLite
        """
        sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])

        guid = job_desc['Id']
        jid = None
        simId = job_desc['Simulation']

        # Run the job
        db.add_message("consumer={0}, starting job {1}"\
            .format(db.consumer_id, jid), guid)

        _log.debug("setup foqus")
        db.job_change_status(guid, "setup")

        configContent = db.get_configuration_file(simId)

        logging.getLogger("foqus." + __name__)\
            .info("Job {0} is submitted".format(jid))

        #db.jobConsumerID(guid, consumer_uuid)
        #db.job_prepare(guid, jid, configContent)

        # Load the session file
        dat = Session(useCurrentWorkingDir=True)
        dat.load(sfile, stopConsumers=True)
        dat.loadFlowsheetValues(vfile)

        # dat.flowsheet.nodes.
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = FOQUSAWSConfig.get_instnance().get_simulation_bucket_name()
        flowsheet_name = job_desc['Simulation']
        prefix = '%s/%s' %(user_name,flowsheet_name)
        l = s3.list_objects(Bucket=bucket_name, Prefix=prefix)
        assert 'Contents' in l, "S3 Simulation:  No keys match %s" %prefix
        _log.debug("Process Flowsheet nodes")
        for nkey in dat.flowsheet.nodes:
            if dat.flowsheet.nodes[nkey].turbApp is None:
                continue
            assert len(dat.flowsheet.nodes[nkey].turbApp) == 2, \
                'DAT Flowsheet nodes turbApp is %s' %dat.flowsheet.nodes[nkey].turbApp

            node = dat.flowsheet.nodes[nkey]
            turb_app = node.turbApp[0]
            model_name = node.modelName
            sinter_filename = '/'.join((user_name, flowsheet_name, nkey, '%s.json' %model_name))

            s3_key_list = [i['Key'] for i in l['Contents']]
            assert sinter_filename in s3_key_list, 'missing sinter configuration "%s" not in %s' %(sinter_filename, str(s3_key_list))
            simulation_name = job_desc.get('Simulation')
            #sim_list = node.gr.turbConfig.getSimulationList()
            sim_list = turbine_simulation_script.main_list([node.gr.turbConfig.getFile()])

            _log.info("Node Turbine Simulation Requested: (%s, %s)", turb_app, simulation_name)

            if turb_app == 'ACM':
                model_filename = '%s/%s/%s/%s.acmf' %(user_name, simulation_name,nkey, model_name)
                assert model_filename in s3_key_list, 'missing sinter configuration "%s"' %sinter_filename
            else:
                _log.info("Turbine Application Not Implemented: '%s'", turb_app)
                raise NotImplementedError('Flowsheet Node model type: "%s"' %(str(dat.flowsheet.nodes[nkey].turbApp)))

            sim_d = [i for i in sim_list if i['Name'] == model_name]
            assert len(sim_d) < 2, 'Expecting 0 or 1 entries for simulation %s' %simulation_name
            if len(sim_d) == 0:
                sim_d = None
            else:
                sim_d = sim_d[0]

            prefix = '%s/%s/%s/' %(user_name,job_desc['Simulation'],nkey)
            entry_list = [i for i in l['Contents'] if i['Key'] != prefix and i['Key'].startswith(prefix)]
            sinter_local_filename = None
            update_required = False
            for entry in entry_list:
                _log.debug("ENTRY: %s", entry)
                key = entry['Key']
                etag = entry.get('ETag', "").strip('"')
                file_name = key.split('/')[-1]
                file_path = os.path.join(CURRENT_JOB_DIR, file_name)
                # Upload to TurbineLite
                # if ends with json or acmf
                si_metadata = []
                if key.endswith('.json'):
                    _log.debug('CONFIGURATION FILE')
                    sinter_local_filename = file_path
                    if sim_d:
                        si_metadata = [i for i in sim_d["StagedInputs"] if i['Name'] == 'configuration']
                elif key.endswith('.acmf'):
                    _log.debug('ACMF FILE')
                    if sim_d:
                        si_metadata = [i for i in sim_d["StagedInputs"] if i['Name'] == 'aspenfile']
                else:
                    raise NotImplementedError('Not allowing File "%s" to be staged in' %key)

                assert len(si_metadata) < 2, 'Turbine Error:  Too many entries for "%s", "%s"' %(simulation_name, file_name)

                # NOTE: Multipart uploads have different ETags ( end with -2  or something )
                #     THus the has comparison will fail
                #     FOr now ignore it, but fixing this check is performance optimization.
                #
                if len(si_metadata) == 1:
                    file_hash = si_metadata[0]['MD5Sum']
                    if file_hash.lower() != etag.lower():
                        _log.debug("Compare %s:  %s != %s" %(file_name, etag, file_hash))
                        _log.debug('s3 download(%s): %s' %(CURRENT_JOB_DIR, key))
                        s3.download_file(bucket_name, key, file_path)
                        update_required = True
                    else:
                        _log.debug("MATCH")
                        s3.download_file(bucket_name, key, file_path)
                else:
                    _log.debug("Add to Turbine Simulation(%s) File: %s" %(simulation_name, file_name))
                    s3.download_file(bucket_name, key, file_path)
                    update_required = True

            assert sinter_local_filename is not None, 'missing sinter configuration file'

            if model_name not in [i['Name'] for i in sim_list]:
                _log.debug('Adding Simulation "%s"' %model_name)
                node.gr.turbConfig.uploadSimulation(model_name, sinter_local_filename, update=False)
            elif update_required:
                # NOTE: Requires the configuration file on update, so must download_file it above...
                _log.debug('Updating Simulation "%s"' %model_name)
                node.gr.turbConfig.uploadSimulation(model_name, sinter_local_filename, update=True)
            else:
                _log.debug('No Update Required for Simulation "%s"' %model_name)

        return dat

    def run_foqus(self, db, dat, job_desc):
        """ Run FOQUS Flowsheet in thread
        db -- TurbineLiteDB instance
        dat -- foqus.framework.session.session
        dat.flowsheet -- foqus.framework.graph.graph
        """
        assert isinstance(db, TurbineLiteDB)
        assert isinstance(dat, Session)
        exit_code = 0
        sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
        guid = job_desc['Id']
        jid = guid # NOTE: like to use actual increment job id but hard to find.
        db.job_change_status(guid, "running")
        gt = dat.flowsheet.runAsThread()
        terminate = False
        while gt.isAlive():
            gt.join(10)
            status = db.consumer_status()
            if status == 'terminate' or self._stop:
                terminate = True
                db.job_change_status(guid, "error")
                gt.terminate()
                break

        if terminate:
            db.add_message("job %s: terminate" %guid, guid)
            return

        if self._stop:
            db.add_message("job %s: windows service stopped" %guid, guid)
            return

        if gt.res[0]:
            dat.flowsheet.loadValues(gt.res[0])
        else:
            dat.flowsheet.errorStat = 19

        dat.saveFlowsheetValues(ofile)
        db.job_save_output(guid, CURRENT_JOB_DIR)
        dat.save(
            filename = rfile,
            updateCurrentFile = False,
            changeLogMsg = "Saved Turbine Run",
            bkp = False,
            indent = 0)

        if dat.flowsheet.errorStat == 0:
            db.job_change_status(guid, "success")
            db.add_message(
                "consumer={0}, job {1} finished, success"\
                    .format(db.consumer_id, jid), guid)
        else:
            db.job_change_status(guid, "error")
            db.add_message(
                "consumer={0}, job {1} finished, error"\
                    .format(db.consumer_id, jid), guid)

        _log.info("Job {0} finished".format(jid))

        #stop all Turbine consumers
        dat.flowsheet.turbConfig.stopAllConsumers()
        dat.flowsheet.turbConfig.closeTurbineLiteDB()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)
