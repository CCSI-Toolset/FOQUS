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
import sys,json,signal,os,errno,uuid,threading,time
from os.path import expanduser
import urllib2
from foqus_lib.framework.session.session import session as Session
from turbine.commands import turbine_simulation_script
import logging
import logging.config
import foqus_worker

_instanceid = None
HOME = expanduser("~")
DEBUG = False
logging.basicConfig(filename='C:\Users\Administrator\FOQUS-Cloud-Service.log',level=logging.DEBUG)
_log = logging.getLogger()
_log.debug('Loading')


class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "FOQUS-Cloud-Service"
    _svc_display_name_ = "FOQUS Cloud Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self.stop = False
        self._instanceid = "UNKNOWN"

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def set_stop(self, value):
        self._stop = value

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        _log.debug("stop called")
        self.stop = True

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))

        _log.debug("starting")
        VisibilityTimeout = 300
        if DEBUG:
            VisibilityTimeout = 0
        try:
            self._instanceid = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read()
        except:
            pass

        if self.stop: return

        job_desc = self.pop_job(VisibilityTimeout=VisibilityTimeout)

        db = foqus_worker.TurbineLiteDB()
        db.consumer_register()
        kat = _KeepAliveTimer(db, freq=60)
        kat.start()
        dat = None

        try:
            dat = self.setup_foqus(db, job_desc)
        except NotImplementedError, ex:
            _log.debug("FOQUS NotImplementedError: %s", ex)
            db.job_change_status(job_desc['Id'], "error")
            db.add_message("job %s: failed in setup", job_desc['Id'])

        if dat is not None:
            self.run_foqus(db, dat, job_desc)

        if not DEBUG:
            # DELETE received message from queue
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )

    def pop_job(self, VisibilityTimeout):
        """ Pop job from AWS SQS, Download FOQUS Flowsheet from AWS S3

        SQS Job Body Contain Job description, for example:
        [{"Initialize":false,
        "Input":{},
        "Reset":false,
        "Simulation":"BFB_v11_FBS_01_26_2018",
        "Visible":false,
        "Id":"8a3033b4-6de2-409c-8552-904889929704"}]
        """
        _instanceid = self._instanceid

        sqs = boto3.client('sqs', region_name='us-east-1')
        queue_url = 'https://sqs.us-east-1.amazonaws.com/754323349409/FOQUS-Job-Queue'
        # Receive message from SQS queue
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=VisibilityTimeout,
            WaitTimeSeconds=0
        )
        if not response.get("Messages", None):
            _log.info("Job Queue is Empty")
            return

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        body = json.loads(message['Body'])
        job_desc = json.loads(body['Message'])
        _log.info('Job Desription: ' + body['Message'])

        sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
        with open(vfile,'w') as fd:
            json.dump(dict(input=job_desc['Input']), fd)

        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'foqus-simulations'
        l = s3.list_objects(Bucket=bucket_name, Prefix='anonymous/%s' %job_desc['Simulation'])
        # BFB_OUU_MultVar_04.09.2018.foqus
        if not l.has_key('Contents'):
            _log.info("S3 Simulation:  No keys match %s" %'anonymous/%s' %job_desc['Simulation'])
            return

        foqus_keys = filter(lambda i: i['Key'].endswith('.foqus'), l['Contents'])
        if len(foqus_keys) == 0:
            _log.info("S3 Simulation:  No keys match %s" %'anonymous/%s/*.foqus' %job_desc['Simulation'])
            return
        if len(foqus_keys) > 1:
            _log.error("S3 Simulations:  Multiple  %s" %str(foqus_keys))
            return

        _log.info("S3: Download Key %s", foqus_keys[0])
        s3.download_file(bucket_name, foqus_keys[0]['Key'], sfile)

        # WRITE CURRENT JOB TO FILE
        with open(os.path.join(foqus_worker.workingDirectory, 'current_foqus.json'), 'w') as fd:
            json.dump(job_desc, fd)

        return job_desc


    def setup_foqus(self, db, job_desc):
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
        bucket_name = 'foqus-simulations'
        l = s3.list_objects(Bucket=bucket_name, Prefix='anonymous/%s' %job_desc['Simulation'])
        if not l.has_key('Contents'):
            _log.info("S3 Simulation:  No keys match %s" %'anonymous/%s' %job_desc['Simulation'])
            return

        _log.debug("Process Flowsheet nodes")
        for nkey in dat.flowsheet.nodes:
            if dat.flowsheet.nodes[nkey].turbApp is None:
                continue
            assert len(dat.flowsheet.nodes[nkey].turbApp) == 2, \
                'DAT Flowsheet nodes turbApp is %s' %dat.flowsheet.nodes[nkey].turbApp

            node = dat.flowsheet.nodes[nkey]
            turb_app = node.turbApp[0]
            model_name = node.modelName
            sinter_filename = 'anonymous/%s/%s/%s.json' %(job_desc['Simulation'],nkey, model_name)
            s3_key_list = map(lambda i: i['Key'] , l['Contents'])
            assert sinter_filename in s3_key_list, 'missing sinter configuration "%s" not in %s' %(sinter_filename, str(s3_key_list))
            simulation_name = job_desc.get('Simulation')
            #sim_list = node.gr.turbConfig.getSimulationList()
            sim_list = turbine_simulation_script.main_list([node.gr.turbConfig.getFile()])

            log.info("Node Turbine Simulation Requested: (%s, %s)", turb_app, simulation_name)

            if turb_app == 'ACM':
                model_filename = 'anonymous/%s/%s/%s.acmf' %(simulation_name,nkey, model_name)
                assert model_filename in s3_key_list, 'missing sinter configuration "%s"' %sinter_filename
            else:
                log.info("Turbine Application Not Implemented: '%s'", turb_app)
                raise NotImplementedError, 'Flowsheet Node model type: "%s"' %(str(dat.flowsheet.nodes[nkey].turbApp))

            sim_d = filter(lambda i: i['Name'] == model_name, sim_list)
            assert len(sim_d) < 2, 'Expecting 0 or 1 entries for simulation %s' %simulation_name
            if len(sim_d) == 0:
                sim_d = None
            else:
                sim_d = sim_d[0]

            prefix = 'anonymous/%s/%s/' %(job_desc['Simulation'],nkey)
            entry_list = filter(lambda i: i['Key'] != prefix and i['Key'].startswith(prefix), l['Contents'])
            sinter_local_filename = None
            update_required = False
            for entry in entry_list:
                _log.debug("ENTRY: %s", entry)
                key = entry['Key']
                etag = entry.get('ETag', "").strip('"')
                file_name = key.split('/')[-1]
                file_path = os.path.join(foqus_worker.workingDirectory, file_name)
                # Upload to TurbineLite
                # if ends with json or acmf
                si_metadata = []
                if key.endswith('.json'):
                    _log.debug('CONFIGURATION FILE')
                    sinter_local_filename = file_path
                    if sim_d:
                        si_metadata = filter(lambda i: i['Name'] == 'configuration', sim_d["StagedInputs"])
                elif key.endswith('.acmf'):
                    _log.debug('ACMF FILE')
                    if sim_d:
                        si_metadata = filter(lambda i: i['Name'] == 'aspenfile', sim_d["StagedInputs"])
                else:
                    raise NotImplementedError, 'Not allowing File "%s" to be staged in' %key

                assert len(si_metadata) < 2, 'Turbine Error:  Too many entries for "%s", "%s"' %(simulation_name, file_name)

                # NOTE: Multipart uploads have different ETags ( end with -2  or something )
                #     THus the has comparison will fail
                #     FOr now ignore it, but fixing this check is performance optimization.
                #
                if len(si_metadata) == 1:
                    file_hash = si_metadata[0]['MD5Sum']
                    if file_hash.lower() != etag.lower():
                        _log.debug("Compare %s:  %s != %s" %(file_name, etag, file_hash))
                        _log.debug('s3 download(%s): %s' %(foqus_worker.workingDirectory, key))
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

            if model_name not in map(lambda i: i['Name'], sim_list):
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
        """
        Run FOQUS Flowsheet in thread
        """
        exit_code = 0
        sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
        guid = job_desc['Id']

        db.job_change_status(guid, "running")
        gt = dat.flowsheet.runAsThread()
        terminate = False
        while gt.isAlive():
            gt.join(10)
            status = db.consumer_status()
            if status == 'terminate' or self.stop:
                terminate = True
                db.job_change_status(guid, "error")
                gt.terminate()
                break

        if terminate:
            db.add_message("job %s: terminate" %guid)
            return

        if self.stop:
            db.add_message("job %s: windows service stopped" %guid)
            return

        if gt.res[0]:
            dat.flowsheet.loadValues(gt.res[0])
        else:
            dat.flowsheet.errorStat = 19

        dat.saveFlowsheetValues(ofile)
        db.job_save_output(guid, foqus_worker.workingDirectory)
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

        _logging.info("Job {0} finished".format(jid))

        #stop all Turbine consumers
        dat.flowsheet.turbConfig.stopAllConsumers()
        dat.flowsheet.turbConfig.closeTurbineLiteDB()

        #sys.exit(exit_code)
        return exit_code


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)
