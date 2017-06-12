import json
from dmf_lib.dialogs.status_dialog import StatusDialog
from dmf_lib.common.common import CCSI_EMBEDDED_METADATA
from dmf_lib.common.common import CCSI_EMBEDDED_INPUT
from dmf_lib.common.common import CCSI_SIM_ID_KEY
from dmf_lib.common.common import CCSI_SIM_DISPLAY_NAME


class SharedOps():
    def aggregateStatuses(self, s_stats, f_stats, tmp_s_stats, tmp_f_stats):
        s_stats += tmp_s_stats
        f_stats += tmp_f_stats

    def editSinterConfigFileMetadata(
            self,
            bytestream,
            sim_id,
            sim_name,
            resource_id_ls,
            resource_name_ls):
        sinter_config_data = json.loads(bytestream.decode('utf-8'))
        resource_id_key = "Resource ID"
        resource_display_name = "Resource Display Name"
        try:
            try:
                # Update if present
                sinter_config_data[CCSI_EMBEDDED_METADATA]
                sinter_config_data[
                    CCSI_EMBEDDED_METADATA][CCSI_SIM_DISPLAY_NAME] = sim_name
                sinter_config_data[CCSI_EMBEDDED_METADATA][
                    CCSI_SIM_ID_KEY] = sim_id
            except:
                # CCSIFileMetaData block not available
                sinter_config_data[CCSI_EMBEDDED_METADATA] \
                    = {CCSI_SIM_ID_KEY: sim_id,
                       CCSI_SIM_DISPLAY_NAME: sim_name}

            # Add resource into InputFiles block
            for id, name in zip(resource_id_ls, resource_name_ls):
                try:
                    addedNew = False
                    for i in xrange(
                            len(sinter_config_data[
                                CCSI_EMBEDDED_METADATA][CCSI_EMBEDDED_INPUT])):
                        current_file_metadata = sinter_config_data[
                            CCSI_EMBEDDED_METADATA][
                                CCSI_EMBEDDED_INPUT][i][CCSI_EMBEDDED_METADATA]
                        if current_file_metadata[
                                resource_display_name] == name:
                            current_file_metadata[resource_id_key] = id
                            addedNew = True
                            break
                    if not addedNew:
                        sinter_config_data[
                            CCSI_EMBEDDED_METADATA][
                                CCSI_EMBEDDED_INPUT].append(
                                    {CCSI_EMBEDDED_METADATA:
                                     {resource_id_key: id,
                                      resource_display_name: name}})
                except:
                    sinter_config_data[CCSI_EMBEDDED_METADATA][CCSI_EMBEDDED_INPUT] = \
                        [{CCSI_EMBEDDED_METADATA:
                          {resource_id_key: id,
                           resource_display_name: name}}]
        except Exception, e:
            if self.verbose:
                print e
            StatusDialog.displayStatus(str(e))

        return bytearray(
            json.dumps(
                sinter_config_data, 'utf-8', sort_keys=True,
                indent=4, separators=(',', ': ')))
