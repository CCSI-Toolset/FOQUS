import os
import json
import uuid
import shutil
import logging
import platform
import collections

from dmf_lib.common.methods import Common

from dmf_lib.common.common import PRINT_COLON
from dmf_lib.common.common import DMF_CREATOR
from dmf_lib.common.common import WINDOWS
from dmf_lib.git.meta_dict import DISPLAY_NAME
from dmf_lib.git.meta_dict import ORIGINAL_NAME
from dmf_lib.git.meta_dict import DESCRIPTION
from dmf_lib.git.meta_dict import CREATOR
from dmf_lib.git.meta_dict import CHECKSUM
from dmf_lib.git.meta_dict import CHECK_IN_COMMENT
from dmf_lib.git.meta_dict import DEPENDENCIES
from dmf_lib.git.meta_dict import MIMETYPE
from dmf_lib.git.meta_dict import EXTERNAL
from dmf_lib.git.meta_dict import VERSION_REQ
from dmf_lib.git.meta_dict import CONFIDENCE
from dmf_lib.git.meta_dict import MAJOR_VERSION
from dmf_lib.git.meta_dict import MINOR_VERSION
try:
    from git import Repo
    from git import Git
except Exception, e:
    print "Error importing git:", e


class GitOps():
    __init_tag = "Initialized"
    __metadata_change_tag = "Metadata changed"
    __physical_change_tag = "Physical commit"
    __git_ignore = ".gitignore"
    __git_master = "master"
    __git_k_v_spacing = ' '*3
    __date_commit_line = 3
    __pre_dict_separator = '\n'*2
    __id_line = 4
    __desc_line = 5
    __grep = "--grep="
    __localdate = "--date=local"

    def __init__(self, parent, user):
        self.root = parent
        self.user = user
        self.verbose = self.root.verbose
        if platform.system().startswith(WINDOWS):
            Git.USE_SHELL = True

    def _addGitIgnore(self, folder_path):
        """
        _addGitIgnore is for adding a .gitignore file so that
        folders can be added to versioned by git.
        """
        open(os.path.join(folder_path, self.__git_ignore), 'wb').close()

    def _getDMFID(self, path=None):
        """
        _getDMFID will return an existing ID for a
        data object if it has a mapped object.
        Otherwise, a new ID is generated.
        """

        dmf_id = None
        if self.git and path:
            grep_opt = (
                self.__grep +
                PRINT_COLON +
                self.handleGrepPath(path) +
                '$')
            log = self.git.log(grep_opt)
            log_split = log.split("\n")
            existing_id = log_split[self.__id_line]
            dmf_id = existing_id.strip()
        else:
            dmf_id = str(uuid.uuid4())
        return dmf_id + '\n'

    def _createFolder(self, folder_path):
        os.mkdir(folder_path)
        self._addGitIgnore(folder_path)

    def _getLogByDMFID(self, dmf_id, major_version, minor_version):
        if self.git:
            grep_id_opt = self.__grep + dmf_id.strip() + '$'
            major_grep_opt = (
                self.__grep + "\"major_version\": " + str(major_version))
            minor_grep_opt = (
                self.__grep + "\"minor_version\": " + str(minor_version))
            and_opt = "--all-match"
            first_entry_opt = "-1"
            log = self.git.log(
                grep_id_opt,
                major_grep_opt,
                minor_grep_opt,
                and_opt,
                first_entry_opt)
            return log
        return None

    def _getChecksumByVersion(
            self,
            major_version,
            minor_version,
            path=None,
            dmf_id=None):
        if self.git:
            if dmf_id:
                dmf_id = dmf_id
            elif path:
                # get DMF ID if not provided
                dmf_id = self._getDMFID(path)
            log = self._getLogByDMFID(dmf_id, major_version, minor_version)
            commit_msg_e = log.split("\n")
            commit_checksum_line = commit_msg_e[0].split(' ')
            checksum = commit_checksum_line[len(commit_checksum_line)-1]
            return checksum
        return None

    def getDMFID(self, path):
        dmf_id = self._getDMFID(path)
        major_version, minor_version = self.getLatestVersion(path)
        return (
            str(dmf_id)[:-1] +
            ';' +
            str(major_version) +
            '.' +
            str(minor_version))

    def isGitInstalled(self):
        try:
            Git().version_info
            return True
        except:
            return False

    def doesDMFIDExist(self, dmf_id):
        if self.git:
            grep_opt = self.__grep + dmf_id + '$'
            log = self.git.log(grep_opt)
            if log:
                log_split = log.split("\n")
                existing_id = log_split[self.__id_line]
                logging.getLogger("foqus." + __name__).debug(
                    "existing id: {d}".format(d=existing_id))
                logging.getLogger("foqus." + __name__).debug(
                    "existing id: {d}".format(d=existing_id.strip()))
                logging.getLogger("foqus." + __name__).debug(
                    "existing id: {d}".format(d=dmf_id))

                return True if existing_id.strip() == dmf_id else False
            else:
                return False
        return None

    def createRepo(self, repo_path):
        if os.path.exists(repo_path):
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "DMF lite repo exists. Will not create new repo."
            self.repo = Repo(repo_path)
        else:
            os.mkdir(repo_path)
            self.repo = Repo.init(repo_path, bare=False)
            config = self.repo.config_writer()
            config.set_value("user", "email", self.user + '@dmf.repo')
            config.set_value("user", "name", self.user)

        self.repo_index = self.repo.index
        self.git = Git(repo_path)
        # Initialized other system folder too
        status = self.createUserFolder(os.path.join(repo_path, self.user))
        if status:
            user_folder = os.path.join(repo_path, self.user)
            self.createSystemFolder(
                os.path.join(user_folder, "Simulation"),
                "Folder for storing simulation files.")
            self.createSystemFolder(
                os.path.join(user_folder, "Sorbentfit"),
                "Folder for storing sorbent fit.")
        return self.repo_index

    def createUserFolder(self, folder_path):
        folder_name = self.user
        description = "DMF lite repo user space for " + folder_name
        return self.createSystemFolder(folder_path, description)

    def createSystemFolder(self, folder_path, description):
        if os.path.exists(folder_path):
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, \
                    "Folder {f} exists.".format(f=folder_path)
            return False
        try:
            self._createFolder(folder_path)
            folder_id = self._getDMFID()
            # Create commit description
            commit_desc = self.__init_tag + PRINT_COLON + folder_path
            # Create dictionary and store metadata
            meta = dict()
            meta[DISPLAY_NAME] = os.path.basename(folder_path)
            meta[DESCRIPTION] = description
            meta[CREATOR] = DMF_CREATOR
            self.repo_index.add([folder_path])
            self.repo_index.commit(
                folder_id +
                commit_desc +
                self.__pre_dict_separator +
                json.dumps(meta))
            return True
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e
            return e

    def createFolder(self, folder_path, folder_name, description):
        try:
            self._createFolder(folder_path)
            folder_id = self._getDMFID()
            # Create commit description
            commit_desc = self.__init_tag + PRINT_COLON + folder_path
            # Create dictionary and store metadata
            meta = dict()
            meta[DISPLAY_NAME] = folder_name
            meta[DESCRIPTION] = description
            meta[CREATOR] = self.user
            self.repo_index.add([folder_path])
            self.repo_index.commit(
                folder_id +
                commit_desc +
                self.__pre_dict_separator +
                json.dumps(meta))
            return True
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e
            return e

    def createVersionedDocument(
            self,
            src_bytestream,
            target_path,
            original_name,
            description,
            mimetype,
            external,
            confidence,
            version_requirements,
            creator,
            version=None,
            dependencies=None,
            check_in_comment=None):
        status = True
        err_msg = None
        f = open(target_path, 'wb')
        try:
            f.write(src_bytestream)
            # Create dictionary and store metadata
            meta = dict()
            meta[DISPLAY_NAME] = os.path.basename(target_path)
            meta[ORIGINAL_NAME] = original_name
            meta[DESCRIPTION] = description
            meta[MIMETYPE] = mimetype
            meta[CREATOR] = self.user
            meta[VERSION_REQ] = version_requirements
            meta[EXTERNAL] = external
            meta[CONFIDENCE] = confidence
            meta[CHECKSUM] = Common().getChecksum(src_bytestream)
            meta[DEPENDENCIES] = dependencies if dependencies else []
            if version:
                meta[MAJOR_VERSION] = version[0]
                meta[MINOR_VERSION] = version[1]
                doc_id = self._getDMFID(target_path)
                # Create commit description
                commit_desc = "Created new version for : " + target_path
            else:
                meta[MAJOR_VERSION] = 1
                meta[MINOR_VERSION] = 0
                doc_id = self._getDMFID()
                # Create commit description
                commit_desc = self.__init_tag + PRINT_COLON + target_path
                # Commit to git repository with commit description
                # and metadata dict
            if check_in_comment:
                meta[CHECK_IN_COMMENT] = check_in_comment
        except Exception, e:
            print self.__class__.__name__, PRINT_COLON, e
            err_msg = e
            status = False
        finally:
            f.close()
            if status:
                try:
                    meta_entry = json.dumps(meta)
                    message = (
                        doc_id +
                        commit_desc +
                        self.__pre_dict_separator +
                        meta_entry)
                    # This works for git version 2.6.x
                    self.repo_index.add([target_path])
                    self.repo_index.commit(message=message)
                    # else:
                    #     # This was tested and worked on version 2.5.x
                    #     self.repo.git.add(target_path)
                    #     self.repo.git.commit(message=message)
                    # message = (
                    #     doc_id +
                    #     self.__physical_change_tag +
                    #     PRINT_COLON +
                    #     target_path +
                    #     self.__pre_dict_separator +
                    #     meta_entry)
                except Exception, e:
                    print self.__class__.__name__, PRINT_COLON, e
                    err_msg = e
                    status = False
            return status, err_msg

    def getCreationDate(self, path):
        if self.git:
            # get DMF ID
            dmf_id = self._getDMFID(path)
            # '$' indicates end of line for exact match
            grep_id_opt = self.__grep + dmf_id.strip() + '$'
            and_opt = "--all-match"
            date_opt = self.__localdate
            if os.path.isdir(path):
                grep_init_opt = self.__grep + self.__init_tag
                log = self.git.log(
                    grep_init_opt,
                    grep_id_opt,
                    and_opt,
                    date_opt)
            else:
                major_grep_opt = (
                    self.__grep + "\"major_version\": 1")
                minor_grep_opt = (
                    self.__grep + "\"minor_version\": 0")
                log = self.git.log(
                    major_grep_opt,
                    minor_grep_opt,
                    grep_id_opt,
                    and_opt,
                    date_opt)
            date_line = log.split("\n")[self.__date_commit_line-1]
            date_line_e = date_line.split(self.__git_k_v_spacing)
            date_str = date_line_e[len(date_line_e)-1]
            return date_str
        return None

    def getLastModifiedDate(self, path):
        if self.git:
            # '$' indicates end of line for exact match
            grep_opt = self.__grep + self.handleGrepPath(path) + '$'
            date_opt = self.__localdate
            log = self.git.log(grep_opt, date_opt)
            date_line = log.split("\n")[self.__date_commit_line-1]
            date_line_e = date_line.split(self.__git_k_v_spacing)
            date_str = date_line_e[len(date_line_e)-1]
            return date_str
        return None

    def getLatestPath(self, dmf_id):
        if self.git:
            grep_id_opt = self.__grep + dmf_id.strip() + '$'
            log = self.git.log(grep_id_opt)
            commit_msg_e = log.split("\n")
            path = commit_msg_e[self.__desc_line].split(':', 1)[1].strip()
            return path
        return None

    def getLatestVersion(self, path):
        meta = self.getLatestMeta(path)
        major_version = meta.get(MAJOR_VERSION)
        minor_version = meta.get(MINOR_VERSION)
        return major_version, minor_version

    def getLatestMeta(self, path):
        if self.git:
            print_opt = "--pretty=%B"
            grep_opt = self.__grep + self.handleGrepPath(path) + '$'
            first_entry_opt = "-1"
            log = self.git.log(grep_opt, print_opt, first_entry_opt).strip()
            commit_msg_e = log.split("\n")
            meta_line = commit_msg_e[len(commit_msg_e)-1]
            meta = json.loads(meta_line.strip())
            return meta
        return None

    def getCreationDateByVersion(self, path, major_version, minor_version):
        if self.git:
            # get DMF ID
            dmf_id = self._getDMFID(path)
            grep_id_opt = self.__grep + dmf_id.strip() + '$'
            major_grep_opt = (
                self.__grep + "\"major_version\": " + str(major_version))
            minor_grep_opt = (
                self.__grep + "\"minor_version\": " + str(minor_version))
            and_opt = "--all-match"
            date_opt = self.__localdate
            log = self.git.log(
                grep_id_opt, major_grep_opt, minor_grep_opt, and_opt, date_opt)
            date_line = log.split("\n")[self.__date_commit_line-1]
            date_line_e = date_line.split(self.__git_k_v_spacing)
            date_str = date_line_e[len(date_line_e)-1]
            return date_str
        return None

    def getMetaByDMFID(self, dmf_id, major_version, minor_version):
        if self.git:
            log = self._getLogByDMFID(dmf_id, major_version, minor_version)
            commit_msg_e = log.split("\n")
            meta_line = commit_msg_e[len(commit_msg_e)-1]
            meta = json.loads(meta_line.strip())
            return meta
        return None

    def getMetaByPath(self, path, major_version, minor_version):
        if self.git:
            # get DMF ID
            dmf_id = self._getDMFID(path)
            return self.getMetaByDMFID(dmf_id, major_version, minor_version)
        return None

    def doesDMFIDHaveLatestVersion(self, dmf_id):
        dmf_id, version = Common().splitDMFID(dmf_id)

        if self.git:
            path = self.getLatestPath(dmf_id)
            major_version, minor_version = self.getLatestVersion(path)
            latest_version = Common().concatVersion(
                major_version, minor_version)
            return True if version == latest_version else False
        return None

    def getChecksumByPathAndVersion(self, major_version, minor_version, path):
        return self._getChecksumByVersion(
            major_version, minor_version, path=path)

    def getChecksumByIDAndVersion(self, major_version, minor_version, dmf_id):
        return self._getChecksumByVersion(
            major_version, minor_version, dmf_id=dmf_id)

    def getPathByDMFID(self, dmf_id, major_version, minor_version):
        if self.git:
            log = self._getLogByDMFID(dmf_id, major_version, minor_version)
            commit_msg_e = log.split("\n")
            path = commit_msg_e[self.__desc_line].split(':', 1)[1].strip()
            return path
        return None

    def getPathByChecksum(self, checksum):
        if self.git:
            first_entry_opt = "-1"
            log = self.git.log(checksum, first_entry_opt)
            commit_msg_e = log.split("\n")
            path = commit_msg_e[self.__desc_line].split(':', 1)[1].strip()
            return path
        return None

    def editFolderMeta(self, path, folder_name, description, fixed_form):
        if self.git:
            new_path = os.path.join(os.path.dirname(path), folder_name)
            folder_id = self._getDMFID(path)
            commit_desc = self.__metadata_change_tag + PRINT_COLON + new_path
            # Create dictionary and store metadata
            meta = dict()
            meta[DISPLAY_NAME] = folder_name
            meta[DESCRIPTION] = description
            meta[CREATOR] = self.user
            if folder_name != os.path.basename(path):
                self.git.mv(path, new_path)  # Rename
            self.repo_index.commit(
                folder_id +
                commit_desc +
                self.__pre_dict_separator +
                json.dumps(meta))

    def editDocumentMetadata(
            self, path, display_name, original_name,
            description, mimetype, external, version_requirements,
            confidence, parent_ids, major_version, minor_version):
        if self.git:
            new_path = os.path.join(os.path.dirname(path), display_name)
            doc_id = self._getDMFID(path)
            commit_desc = self.__metadata_change_tag + PRINT_COLON + new_path
            prev_meta = self.getLatestMeta(path)
            # Create dictionary and store metadata
            meta = dict()
            meta[DISPLAY_NAME] = display_name
            meta[ORIGINAL_NAME] = original_name
            meta[DESCRIPTION] = description
            meta[MIMETYPE] = mimetype
            meta[CREATOR] = self.user
            meta[EXTERNAL] = external
            meta[VERSION_REQ] = version_requirements
            meta[CONFIDENCE] = confidence
            meta[CHECKSUM] = prev_meta[CHECKSUM]
            meta[DEPENDENCIES] = prev_meta[DEPENDENCIES]
            meta[MAJOR_VERSION] = major_version
            meta[MINOR_VERSION] = int(minor_version) + 1
            meta_entry = json.dumps(meta)

            if display_name != os.path.basename(path):
                message = (
                    doc_id +
                    commit_desc +
                    self.__pre_dict_separator +
                    meta_entry)
                self.git.mv(path, new_path)  # Rename
                self.repo.git.commit(message=message)
            else:
                self.repo_index.commit(
                    doc_id +
                    commit_desc +
                    self.__pre_dict_separator +
                    meta_entry)

    def getVersionList(self, path):
        if self.git:
            dmf_id = self._getDMFID(path)
            grep_id_opt = self.__grep + dmf_id.strip() + '$'
            log = self.git.log(grep_id_opt)
            commit_msg_e = log.split("\n")
            version_list = []
            for l in commit_msg_e:
                try:
                    meta = json.loads(l.strip())
                    version = "{major}.{minor}".format(
                        major=meta.get(MAJOR_VERSION),
                        minor=meta.get(MINOR_VERSION))
                    version_list.append(version)
                except:
                    continue
            return collections.OrderedDict.fromkeys(version_list).keys()
        return None

    def downloadFile(self, path, version, dst_path=None):
        if self.git:
            status = True
            status_msg = None
            try:
                version = version.split('.')
                checksum = self.getChecksumByPathAndVersion(
                    version[0], version[1], path=path)
                src_path = self.getPathByChecksum(checksum)
                self.git.checkout(checksum)
                if dst_path:
                    shutil.copy2(src_path, dst_path)
                    self.git.checkout(self.__git_master)
                else:
                    f = open(src_path, 'rb')
                    data = f.read()
                    f.close()
                    self.git.checkout(self.__git_master)
                    return data
            except Exception, e:
                if self.verbose:
                    print self.__class__.__name__, PRINT_COLON, e
                status_msg = e
                status = False
        return status, status_msg

    def downloadFolder(self, src_path, dst_path):
        status = True
        status_msg = None
        try:
            shutil.copytree(src_path, dst_path)
            status = True
        except Exception, e:
            if self.verbose:
                print self.__class__.__name__, PRINT_COLON, e
            status_msg = e
            status = False
        return status, status_msg

    def handleGrepPath(self, path):
        if platform.system().startswith(WINDOWS):
            return path.replace("\\", "\\\\")
        else:
            return path

    def getNewVersion(self, path, is_major_version):
        major_version, minor_version = self.getLatestVersion(path)
        if is_major_version:
            major_version += 1
            minor_version = 0
        else:
            minor_version += 1
        return (major_version, minor_version)

    def isFileContentsIdentical(self, incoming_bytestream, target_path):
        prev_meta = self.getLatestMeta(target_path)
        return prev_meta[CHECKSUM] == Common().getChecksum(incoming_bytestream)
