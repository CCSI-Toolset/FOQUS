package ccsi.dm.data;

import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.Adler32;
import java.util.zip.CheckedOutputStream;
import java.util.zip.Deflater;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import org.apache.chemistry.opencmis.client.api.CmisObject;
import org.apache.chemistry.opencmis.client.api.Document;
import org.apache.chemistry.opencmis.client.api.Folder;
import org.apache.chemistry.opencmis.client.api.ItemIterable;
import org.apache.chemistry.opencmis.client.api.ObjectId;
import org.apache.chemistry.opencmis.client.api.OperationContext;
import org.apache.chemistry.opencmis.client.api.Property;
import org.apache.chemistry.opencmis.client.api.Session;
import org.apache.chemistry.opencmis.client.runtime.OperationContextImpl;
import org.apache.chemistry.opencmis.commons.PropertyIds;
import org.apache.chemistry.opencmis.commons.data.ContentStream;
import org.apache.chemistry.opencmis.commons.enums.BaseTypeId;
import org.apache.chemistry.opencmis.commons.enums.IncludeRelationships;
import org.apache.chemistry.opencmis.commons.enums.VersioningState;
import org.apache.chemistry.opencmis.commons.exceptions.CmisContentAlreadyExistsException;
import org.apache.chemistry.opencmis.commons.exceptions.CmisObjectNotFoundException;
import org.apache.chemistry.opencmis.commons.exceptions.CmisPermissionDeniedException;
import org.apache.chemistry.opencmis.commons.impl.dataobjects.ContentStreamImpl;
import org.apache.chemistry.opencmis.commons.impl.json.JSONObject;
import org.apache.chemistry.opencmis.commons.impl.json.parser.JSONParseException;
import org.apache.chemistry.opencmis.commons.impl.json.parser.JSONParser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import ccsi.dm.common.Common;
import ccsi.dm.connection.ConnectionClient;

public class DataOperationsImpl implements DataOperations {

	private static Logger log = LoggerFactory.getLogger(DataOperationsImpl.class.getName());

	public enum MetaDataType {
		UNKNOWN, CONFIG_FILE, INPUT_DATA_FILE, RESULTS_DATA_FILE, EXCEL_DATA_FILE, OUTPUT_FILE
	}

	private String PLAIN_TEXT_MIMETYPE = "text/plain";
	private String EXCEL_MIMETYPE = "application/vnd.ms-excel";

	public class SorbentFitSet {
		private String timestamp;
		private ArrayList<String> dependencies;
		private StatusObject status;

		public SorbentFitSet(String timestamp) {
			this.timestamp = timestamp;
			this.dependencies = null;
		}

		public void addDependency(String dependency) {
			if (this.dependencies == null)
				this.dependencies = new ArrayList<String>();
			this.dependencies.add(dependency);
		}

		public void addDependencies(ArrayList<String> dependencies) {
			if (this.dependencies == null)
				this.dependencies = new ArrayList<String>();
			if (dependencies != null) {
				for (String each : dependencies)
					this.dependencies.add(each);
			}
		}

		public String getTimestamp() {
			return this.timestamp;
		}

		public int getNumberOfDependencies() {
			return this.dependencies.size();
		}

		public String getDependency(int index) {
			if (index >= this.dependencies.size())
				return "";
			else
				return this.dependencies.get(index);
		}

		public ArrayList<String> getDependencies() {
			return this.dependencies;
		}

		public void setStatus(StatusObject status) {
			this.status = status;
		}

		public StatusObject getStatus() {
			return this.status;
		}

		public boolean hasCreated() {
			return this.status.isOperationSuccessful();
		}

		public String getDataObjectID() {
			String NODE_PREFIX = "workspace://SpacesStore/";
			String id = this.status.getDataObjectID().replace(NODE_PREFIX, "");
			return id;
		}
	}

	public class FileInfo {
		private String flenameWPath;
		private String displayFile;
		private MetaDataType metaDataType;
		private ArrayList<String> dependencies;

		public FileInfo(String flenameWPath, String displayFile, MetaDataType metaDataType, List<String> dependencies) {
			this.flenameWPath = flenameWPath;
			this.displayFile = displayFile;
			this.metaDataType = metaDataType;
			if (dependencies != null) {
				this.dependencies = new ArrayList<String>();
				for (String each : dependencies)
					this.dependencies.add(each);
			} else
				this.dependencies = null;
		}

		public void addDependency(String dependency) {
			if (this.dependencies == null)
				this.dependencies = new ArrayList<String>();
			this.dependencies.add(dependency);
		}

		public ArrayList<String> getDependencies() {
			return this.dependencies;
		}

		public String getFlenameWPath() {
			return this.flenameWPath;
		}

		public String getDisplayFile() {
			return this.displayFile;
		}

		public MetaDataType getMetaDataType() {
			return this.metaDataType;
		}
	}

	@Override
	public Folder cmisObject2Folder(CmisObject cmisObject) {

		if (cmisObject.getBaseTypeId() == BaseTypeId.CMIS_FOLDER) {
			return (Folder) cmisObject;
		} else {
			log.error("Failed attempt to convert CmisObject to folder with name: " + cmisObject.getName());
			return null;
		}
	}

	@Override
	public Document cmisObject2Document(CmisObject cmisObject) {

		if (cmisObject.getBaseTypeId() == BaseTypeId.CMIS_DOCUMENT) {
			return (Document) cmisObject;
		} else {
			log.error("Failed attempt to convert CmisObject to document with name: " + cmisObject.getName());
			return null;
		}
	}

	private ArrayList<String> getDependencies(String configFileWPath) {
		BufferedReader bufferedReader = null;
		ArrayList<String> dependencies = null;

		try {
			FileReader fileReader = new FileReader(configFileWPath);
			bufferedReader = new BufferedReader(fileReader);
			String line = null;
			line = bufferedReader.readLine();
			line = bufferedReader.readLine();
			if (line.startsWith("#"))
				line = line.substring(1, line.length());
			line = line.trim();
			if (line.length() == 0)
				return null;

			String[] valueString = line.split(" ");
			if (valueString.length > 0) {
				dependencies = new ArrayList<String>();
				for (int i = 0; i < valueString.length; i++)
					dependencies.add(valueString[i]);
			}

		} catch (IOException e) {
			log.debug(e.getLocalizedMessage());
		} catch (Exception e) {
			log.debug(e.getLocalizedMessage() + " Attempted to get dependencies from file: " + configFileWPath);
		} finally {
			try {
				bufferedReader.close();
			} catch (Exception e) {
				log.error(e.getLocalizedMessage());
				log.error(e.getMessage());
			}
		}
		return dependencies;
	}

	private SorbentFitSet getSorbentFit(ArrayList<SorbentFitSet> arraySorbentFitSet, String timestamp) {
		for (SorbentFitSet each : arraySorbentFitSet) {
			if (each.getTimestamp().equalsIgnoreCase(timestamp) == true) {
				return each;
			}
		}
		return null;
	}

	private StatusObject createSorbentFitMetadata(ArrayList<SorbentFitSet> arraySorbentFitSet,
			SorbentFitSet thisSorbentFit, ConnectionClient c, String fileFolder, String confidence,
			boolean isVersionMajor, String external) {
		String NODE_PREFIX = "workspace://SpacesStore/";
		StatusObject statusObject = new StatusObject();

		StringBuilder stringBuilder = new StringBuilder();

		try {
			List<String> thisDependencyIDArray = null;
			ArrayList<String> dependencies = thisSorbentFit.getDependencies();
			if (dependencies != null) {
				thisDependencyIDArray = new ArrayList<String>();
				for (int i = 0; i < dependencies.size(); i++) {
					SorbentFitSet dependencySorbentFit = getSorbentFit(arraySorbentFitSet, dependencies.get(i));
					if (dependencySorbentFit.hasCreated() == false)
						createSorbentFitMetadata(arraySorbentFitSet, dependencySorbentFit, c, fileFolder, confidence,
								isVersionMajor, external);
					else
						thisDependencyIDArray.add(dependencySorbentFit.getDataObjectID());
				}
			}

			// read filelist file to get data files
			File file = null;
			BufferedReader bufferedReader = null;
			String filelist = "filelist" + thisSorbentFit.getTimestamp() + ".txt";
			ArrayList<String> arrayDataInputFile = new ArrayList<String>();

			try {
				FileReader fileReader = new FileReader(fileFolder + filelist);
				bufferedReader = new BufferedReader(fileReader);
				String line = null;
				int index = 0;
				while ((line = bufferedReader.readLine()) != null) {
					index++;
					if (index < 3)
						continue;
					if (!line.isEmpty())
						arrayDataInputFile.add(line.substring(5, line.length()));
				}
			} catch (IOException e) {
				statusObject.setFailure(e.getLocalizedMessage());
				log.debug(e.getLocalizedMessage());
			} catch (Exception e) {
				statusObject.setFailure(e.getLocalizedMessage());
				log.debug(e.getLocalizedMessage() + " Attempted to read file: " + fileFolder + filelist);
			} finally {
				try {
					bufferedReader.close();
				} catch (Exception e) {
					log.error(e.getLocalizedMessage());
					log.error(e.getMessage());
				}
			}

			Session session = c.getAtomSession();

			Folder sharedFolder = getHighLevelFolder(session, DataFolderMap.SHARED);
			Folder targetFolder = getTargetFolderInParentFolder(session, sharedFolder.getPath(),
					DataFolderMap.SORBENTFIT, true);

			if (targetFolder == null) {
				statusObject = this.createFolder(sharedFolder, DataFolderMap.SORBENTFIT);
				if (statusObject.isOperationSuccessful()) {
					CmisObject cmisObject = session.getObject(statusObject.getDataObjectID());
					targetFolder = cmisObject2Folder(cmisObject);
				}
			}

			List<String> dependencyFilelist = new ArrayList<String>();
			List<String> dependencyOutput = new ArrayList<String>();

			// create data input file
			FileInfo inputDataFileInfo = null;
			for (int i = 0; i < arrayDataInputFile.size(); i++) {
				String dataFile = arrayDataInputFile.get(i);
				inputDataFileInfo = new FileInfo(fileFolder + dataFile, dataFile, MetaDataType.INPUT_DATA_FILE, null);
				statusObject = uploadFile(c, targetFolder, inputDataFileInfo, confidence, isVersionMajor, external);
				stringBuilder.append(statusObject.getDetailsMessage() + "\n");
				if (statusObject.isOperationSuccessful() == false)
					throw new Exception("Failed to create file: " + fileFolder + dataFile);
				String id = statusObject.getDataObjectID().replace(NODE_PREFIX, "");
				dependencyFilelist.add(id);
			}

			// create filelist file
			FileInfo resultDataFileInfo = new FileInfo(fileFolder + filelist, filelist, MetaDataType.INPUT_DATA_FILE,
					dependencyFilelist);
			statusObject = uploadFile(c, targetFolder, resultDataFileInfo, confidence, isVersionMajor, external);
			stringBuilder.append(statusObject.getDetailsMessage() + "\n");
			if (statusObject.isOperationSuccessful() == false)
				throw new Exception("Failed to create file: " + fileFolder + filelist);
			String id_filelist = statusObject.getDataObjectID().replace(NODE_PREFIX, "");
			dependencyOutput.add(id_filelist);

			// create config file
			String configFile = "config" + thisSorbentFit.getTimestamp() + ".txt";
			FileInfo configFileInfo = new FileInfo(fileFolder + configFile, configFile, MetaDataType.CONFIG_FILE,
					thisDependencyIDArray);
			statusObject = uploadFile(c, targetFolder, configFileInfo, confidence, isVersionMajor, external);
			stringBuilder.append(statusObject.getDetailsMessage() + "\n");
			if (statusObject.isOperationSuccessful() == false)
				throw new Exception("Failed to create file: " + fileFolder + configFile);
			String id_config = statusObject.getDataObjectID().replace(NODE_PREFIX, "");
			dependencyOutput.add(id_config);

			// create data output file
			FileInfo outputDataFileInfo = null;
			for (int i = 0; i < arrayDataInputFile.size(); i++) {
				String dataFile = "data" + thisSorbentFit.getTimestamp() + "_" + Integer.toString(i) + ".txt";
				outputDataFileInfo = new FileInfo(fileFolder + dataFile, dataFile, MetaDataType.RESULTS_DATA_FILE,
						dependencyOutput);
				statusObject = uploadFile(c, targetFolder, outputDataFileInfo, confidence, isVersionMajor, external);
				stringBuilder.append(statusObject.getDetailsMessage() + "\n");
				if (statusObject.isOperationSuccessful() == false)
					throw new Exception("Failed to create file: " + fileFolder + dataFile);
			}

			// create output
			String outputFile = "optresults" + thisSorbentFit.getTimestamp() + ".txt";
			FileInfo outputFileInfo = new FileInfo(fileFolder + outputFile, outputFile, MetaDataType.OUTPUT_FILE,
					dependencyOutput);
			statusObject = uploadFile(c, targetFolder, outputFileInfo, confidence, isVersionMajor, external);
			stringBuilder.append(statusObject.getDetailsMessage() + "\n");
			if (statusObject.isOperationSuccessful() == false)
				throw new Exception("Failed to create file: " + fileFolder + outputFile);
			thisSorbentFit.setStatus(statusObject);

		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
		} finally {
		}
		statusObject.setDetailsMessage(stringBuilder.toString());
		return statusObject;
	}

	public StatusObject createSorbentFitMetadata(ConnectionClient c, String fileFolder, String confidence,
			boolean isVersionMajor, String external) {
		StatusObject statusObject = new StatusObject();

		try {
			fileFolder = fileFolder.replace("\\", Common.FWD_SLASH);
			if (fileFolder.substring(fileFolder.length() - 1).equals(Common.FWD_SLASH) == false)
				fileFolder += Common.FWD_SLASH;

			// first read config file
			File dir = new File(fileFolder);
			if (!dir.exists() || !dir.isDirectory()) {
				throw new Exception("directory: " + fileFolder + " doesn't exist!");
			}

			File ConfigfilesInFolder = new File(fileFolder);
			File[] files = ConfigfilesInFolder.listFiles();
			if (files == null) {
				throw new Exception("No file exist in directory: " + fileFolder);
			}

			ArrayList<SorbentFitSet> arraySorbentFitSet = new ArrayList<SorbentFitSet>();
			SorbentFitSet eachSorbentFitSet = null;
			ArrayList<String> dependencis = null;
			for (File eachFile : files) {
				if (eachFile.isDirectory())
					continue;

				String filename = eachFile.getName();
				if (filename.toLowerCase().startsWith("config") == false)
					continue;

				String timestamp = filename.substring(6, filename.length() - 4);
				eachSorbentFitSet = new SorbentFitSet(timestamp);
				dependencis = getDependencies(fileFolder + filename);
				if (dependencis != null)
					eachSorbentFitSet.addDependencies(dependencis);
				arraySorbentFitSet.add(eachSorbentFitSet);
			}

			StringBuilder stringBuilder = new StringBuilder();
			stringBuilder.append("uploading files from folder: " + fileFolder + "\n\n");
			for (SorbentFitSet each : arraySorbentFitSet) {
				statusObject = createSorbentFitMetadata(arraySorbentFitSet, each, c, fileFolder, confidence,
						isVersionMajor, external);
				stringBuilder.append(statusObject.getDetailsMessage());
				if (statusObject.isOperationSuccessful() == false)
					throw new Exception("Failed to createSorbentFit: " + fileFolder + each.getTimestamp());
				stringBuilder.append("\n");
			}

			statusObject.setDetailsMessage(stringBuilder.toString());
			return statusObject;
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
		} finally {
		}

		return statusObject;
	}

	@Override
	public StatusObject createConfigMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external) {

		return createMetaData(targetFolder, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, null, external, MetaDataType.CONFIG_FILE);
	}

	@Override
	public StatusObject createConfigMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return createMetaData(targetFolder, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.CONFIG_FILE);
	}

	@Override
	public StatusObject createExcelDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external) {

		return createMetaData(targetFolder, documentName, EXCEL_MIMETYPE, confidence, isVersionMajor, null, localPath,
				null, null, null, external, MetaDataType.EXCEL_DATA_FILE);
	}

	@Override
	public StatusObject createExcelDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return createMetaData(targetFolder, documentName, EXCEL_MIMETYPE, confidence, isVersionMajor, null, localPath,
				null, null, parents, external, MetaDataType.EXCEL_DATA_FILE);
	}

	@Override
	public StatusObject createInputDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external) {

		return createMetaData(targetFolder, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, null, external, MetaDataType.INPUT_DATA_FILE);
	}

	@Override
	public StatusObject createInputDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return createMetaData(targetFolder, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.INPUT_DATA_FILE);
	}

	@Override
	public StatusObject createResultsDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external) {

		return createMetaData(targetFolder, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, null, external, MetaDataType.RESULTS_DATA_FILE);
	}

	@Override
	public StatusObject createResultsDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return createMetaData(targetFolder, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.RESULTS_DATA_FILE);
	}

	@Override
	public StatusObject createOutputMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external) {

		return createMetaData(targetFolder, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, null, external, MetaDataType.OUTPUT_FILE);
	}

	@Override
	public StatusObject createOutputMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return createMetaData(targetFolder, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.OUTPUT_FILE);
	}

	@Override
	public StatusObject createVersionedDocument(Folder targetFolder, String documentName, String mimeType,
			String confidence, String localPath, boolean isVersionMajor, String external, String version_requirements) {
		return createDocument(targetFolder, documentName, mimeType, confidence, isVersionMajor, null, localPath, true,
				null, null, null, external, version_requirements);
	}

	@Override
	public StatusObject createVersionedDocument(Folder targetFolder, String documentName, String mimeType,
			String confidence, String localPath, boolean isVersionMajor, String title, String description,
			List<String> parents, String external, String version_requirements) {
		return createDocument(targetFolder, documentName, mimeType, confidence, isVersionMajor, null, localPath, true,
				title, description, parents, external, version_requirements);
	}

	@Override
	public StatusObject createVersionedDocument(Folder targetFolder, String documentName, String mimeType,
			String confidence, ByteArrayInputStream inputStream, boolean isVersionMajor, String title,
			String description, List<String> parents, String external, String version_requirements) {
		return createDocument(targetFolder, documentName, mimeType, confidence, isVersionMajor, inputStream, null, true,
				title, description, parents, external, version_requirements);
	}

	@Override
	public StatusObject createDocument(Folder targetFolder, String documentName, String mimeType, String confidence,
			String localPath, String external, String version_requirements) {
		return createDocument(targetFolder, documentName, mimeType, confidence, false, null, localPath, false, null,
				null, null, external, version_requirements);
	}

	@Override
	public StatusObject createDocument(Folder targetFolder, String documentName, String mimeType, String confidence,
			String title, String description, String localPath, List<String> parents, String external,
			String version_requirements) {
		return createDocument(targetFolder, documentName, mimeType, confidence, false, null, localPath, false, title,
				description, parents, external, version_requirements);
	}

	@Override
	public StatusObject createDocument(Folder targetFolder, String documentName, String mimeType, String confidence,
			ByteArrayInputStream inputStream, List<String> parents, String external, String version_requirements) {

		return createDocument(targetFolder, documentName, mimeType, confidence, false, inputStream, null, false, null,
				null, null, external, version_requirements);
	}

	private StatusObject createDocument(Folder targetFolder, String documentName, String mimeType, String confidence,
			boolean isVersionMajor, ByteArrayInputStream inputStream, String localPath, boolean isVersioned,
			String title, String description, List<String> parents, String external, String version_requirements) {

		File file = null;
		FileInputStream fis = null;
		DataInputStream dis = null;
		String sha1 = null;
		VersioningState versionState;
		StatusObject statusObject = new StatusObject();

		try {
			ContentStream contentStream = null;
			Map<String, Object> properties = new HashMap<String, Object>();

			if (inputStream == null) {
				file = new File(localPath);
				fis = new FileInputStream(file);
				dis = new DataInputStream(fis);
				byte[] bytes = new byte[(int) file.length()];
				dis.readFully(bytes);
				inputStream = new ByteArrayInputStream(bytes);
				/*
				 * Always set mimetype to plain text to allow alfresco search
				 * file contents, actual mimetype to be set in properties.
				 */

				contentStream = new ContentStreamImpl(file.getAbsolutePath(), null, PLAIN_TEXT_MIMETYPE, inputStream);
				properties.put(PropertyIds.NAME, documentName);
			} else {
				contentStream = new ContentStreamImpl(documentName, null, PLAIN_TEXT_MIMETYPE, inputStream);
				properties.put(PropertyIds.NAME, documentName);
			}

			sha1 = this.getChecksum(inputStream);

			try {
				JSONParser parser = new JSONParser();
				JSONObject jsonObject = (JSONObject) parser.parse(new InputStreamReader(inputStream));
				JSONObject flowsheetObject = (JSONObject) jsonObject.get("flowsheet");

				// Populate nodes list
				ArrayList<String> nodes = new ArrayList<String>();
				for (String topLevelKey : flowsheetObject.keySet()) {
					if (topLevelKey.toLowerCase().equals("nodes")) {
						JSONObject nodeProp = (JSONObject) flowsheetObject.get(topLevelKey);
						for (String key : nodeProp.keySet()) {
							nodes.add(key);
						}
					}
				}

				properties.put(DataModelVars.CCSI_SIM, nodes.toString());

			} catch (JSONParseException e) {
				// Handle non-JSON files if needed
			} catch (Exception e) {

			} finally {
				inputStream.reset();
			}

			if (isVersioned) {
				properties.put(PropertyIds.OBJECT_TYPE_ID,
						DataModelVars.D_PREFIX + DataModelVars.CCSI_DOCUMENT_V + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CM_TITLED + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_UPLOAD_ORIGIN + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_DOCUMENT_ASPECT);

			} else {
				properties.put(PropertyIds.OBJECT_TYPE_ID,
						DataModelVars.D_PREFIX + DataModelVars.CCSI_DOCUMENT + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CM_TITLED + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_UPLOAD_ORIGIN + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_DOCUMENT_ASPECT);

				// "D:ccsi:document, P:cm:titled, P:cm:author");
			}

			properties.put(DataModelVars.CCSI_MIMETYPE, mimeType);
			properties.put(DataModelVars.CCSI_CONFIDENCE, confidence);
			properties.put(DataModelVars.CCSI_CHECKSUM, sha1);

			if (title != null) {
				properties.put(DataModelVars.CM_TITLE, title);
			}

			if (description != null) {
				properties.put(DataModelVars.CM_DESCRIPTION, description);
			}

			if (parents != null && !parents.isEmpty()) {
				properties.put(DataModelVars.CCSI_PARENTS, parents);
			}

			if (external != null) {
				properties.put(DataModelVars.CCSI_EXT_LINK, external);
			}

			if (version_requirements != null) {
				properties.put(DataModelVars.CCSI_VER_REQ, version_requirements);
			}

			// properties.put(PropertyIds.OBJECT_TYPE_ID, this.CMIS_DOCUMENT
			// + this.COMMA_SEPARATOR + this.P_PREFIX + this.CM_TITLED
			// + this.COMMA_SEPARATOR + this.P_PREFIX + this.CM_AUTHOR);
			// properties.put(PropertyIds.NAME, documentName);
			// ArrayList<String> arl = new ArrayList<String>();
			// arl.add("(test,1.0)");
			// arl.add("test2");

			// ArrayList<Double> varl = new ArrayList<Double>();
			// varl.add(1.0);
			// varl.add(1.5);

			// if (isVersioned) {
			// properties.put("ccsi:derived-v", arl);
			// properties.put("ccsi:version-derived-v", varl);
			// } else {
			// properties.put("ccsi:derived", arl);
			// properties.put("ccsi:version-derived", varl);
			// }

			// if (author != null) {
			// properties.put(DataModelVars.CM_AUTHOR, author);
			// }

			if (isVersionMajor) {
				versionState = VersioningState.MAJOR;
			} else {
				versionState = VersioningState.MINOR;
			}

			Document document = targetFolder.createDocument(properties, contentStream, versionState);

			statusObject.setSuccess(document.getId());

			return statusObject;

		} catch (FileNotFoundException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.error(e.getLocalizedMessage());
		} catch (IOException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage());
		} catch (CmisContentAlreadyExistsException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document with document name: " + documentName);
		} catch (CmisPermissionDeniedException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document in target folder: " + targetFolder);
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document with document name: " + documentName);
		} finally {
			try {
				if (dis != null) {
					dis.close();
				}

				if (fis != null) {
					fis.close();
				}
			} catch (IOException e) {
				log.error(e.getLocalizedMessage());
				log.error(e.getMessage());
			}
		}

		return statusObject;
	}

	private StatusObject createMetaData(Folder targetFolder, String documentName, String mimeType, String confidence,
			boolean isVersionMajor, ByteArrayInputStream inputStream, String localPath, String title,
			String description, List<String> parents, String external, MetaDataType metaDataType) {

		File file = null;
		FileInputStream fis = null;
		DataInputStream dis = null;
		String sha1 = null;
		VersioningState versionState;
		StatusObject statusObject = new StatusObject();
		String fileContent = "";

		try {
			ContentStream contentStream = null;
			Map<String, Object> properties = new HashMap<String, Object>();

			if (inputStream == null) {
				file = new File(localPath);
				fis = new FileInputStream(file);
				dis = new DataInputStream(fis);
				byte[] bytes = new byte[(int) file.length()];
				dis.readFully(bytes);
				inputStream = new ByteArrayInputStream(bytes);
				fileContent = new String(bytes);

				/*
				 * Always set mimetype to plain text to allow alfresco search
				 * file contents, actual mimetype to be set in properties.
				 */

				if (metaDataType == MetaDataType.EXCEL_DATA_FILE)
					contentStream = new ContentStreamImpl(file.getAbsolutePath(), null, EXCEL_MIMETYPE, inputStream);
				else
					contentStream = new ContentStreamImpl(file.getAbsolutePath(), null, PLAIN_TEXT_MIMETYPE,
							inputStream);
				properties.put(PropertyIds.NAME, documentName);
			} else {
				if (metaDataType == MetaDataType.EXCEL_DATA_FILE)
					contentStream = new ContentStreamImpl(documentName, null, EXCEL_MIMETYPE, inputStream);
				else
					contentStream = new ContentStreamImpl(documentName, null, PLAIN_TEXT_MIMETYPE, inputStream);
				properties.put(PropertyIds.NAME, documentName);
			}

			sha1 = this.getChecksum(inputStream);

			try {
				JSONParser parser = new JSONParser();
				JSONObject jsonObject = (JSONObject) parser.parse(new InputStreamReader(inputStream));
				JSONObject flowsheetObject = (JSONObject) jsonObject.get("flowsheet");

				// Populate nodes list
				ArrayList<String> nodes = new ArrayList<String>();
				for (String topLevelKey : flowsheetObject.keySet()) {
					if (topLevelKey.toLowerCase().equals("nodes")) {
						JSONObject nodeProp = (JSONObject) flowsheetObject.get(topLevelKey);
						for (String key : nodeProp.keySet()) {
							nodes.add(key);
						}
					}
				}

				properties.put(DataModelVars.CCSI_SIM, nodes.toString());

			} catch (JSONParseException e) {
				// Handle non-JSON files if needed
			} catch (Exception e) {

			} finally {
				inputStream.reset();
			}

			properties.put(DataModelVars.CCSI_MIMETYPE, mimeType);
			properties.put(DataModelVars.CCSI_CONFIDENCE, confidence);
			properties.put(DataModelVars.CCSI_CHECKSUM, sha1);

			if (title != null) {
				properties.put(DataModelVars.CM_TITLE, title);
			}

			if (description != null) {
				properties.put(DataModelVars.CM_DESCRIPTION, description);
			}

			if (parents != null && !parents.isEmpty()) {
				properties.put(DataModelVars.CCSI_PARENTS, parents);
			}

			if (external != null) {
				properties.put(DataModelVars.CCSI_EXT_LINK, external);
			}

			// properties.put(PropertyIds.OBJECT_TYPE_ID, this.CMIS_DOCUMENT
			// + this.COMMA_SEPARATOR + this.P_PREFIX + this.CM_TITLED
			// + this.COMMA_SEPARATOR + this.P_PREFIX + this.CM_AUTHOR);
			// properties.put(PropertyIds.NAME, documentName);
			// ArrayList<String> arl = new ArrayList<String>();
			// arl.add("(test,1.0)");
			// arl.add("test2");

			// ArrayList<Double> varl = new ArrayList<Double>();
			// varl.add(1.0);
			// varl.add(1.5);

			// if (isVersioned) {
			// properties.put("ccsi:derived-v", arl);
			// properties.put("ccsi:version-derived-v", varl);
			// } else {
			// properties.put("ccsi:derived", arl);
			// properties.put("ccsi:version-derived", varl);
			// }

			// if (author != null) {
			// properties.put(DataModelVars.CM_AUTHOR, author);
			// }

			if (isVersionMajor) {
				versionState = VersioningState.MAJOR;
			} else {
				versionState = VersioningState.MINOR;
			}

			switch (metaDataType) {
			case CONFIG_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID,
						DataModelVars.D_PREFIX + DataModelVars.CCSI_CONFIGFILE + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CM_TITLED + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_UPLOAD_ORIGIN + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_DOCUMENT_ASPECT);

				if (parseConfigFile(fileContent, properties) == false)
					throw new Exception("failed in calling parseConfigFile");
				break;

			case EXCEL_DATA_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID,
						DataModelVars.D_PREFIX + DataModelVars.CCSI_EXCELDATAFILE + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CM_TITLED + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_UPLOAD_ORIGIN + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_DOCUMENT_ASPECT);

				if (parseExcelDataFile(localPath, properties) == false)
					throw new Exception("failed in calling parseExcelDataFile");
				break;

			case INPUT_DATA_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID,
						DataModelVars.D_PREFIX + DataModelVars.CCSI_DOCUMENT_V + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CM_TITLED + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_UPLOAD_ORIGIN + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_DOCUMENT_ASPECT);
				break;

			case RESULTS_DATA_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID,
						DataModelVars.D_PREFIX + DataModelVars.CCSI_TEXTDATAFILE + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CM_TITLED + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_UPLOAD_ORIGIN + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_DOCUMENT_ASPECT);

				if (parseTextDataFile(fileContent, properties) == false)
					throw new Exception("failed in calling parseTextDataFile for results data file");
				break;

			case OUTPUT_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID,
						DataModelVars.D_PREFIX + DataModelVars.CCSI_OUTPUTFILE + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CM_TITLED + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_UPLOAD_ORIGIN + Common.COMMA_SEPARATOR
								+ DataModelVars.P_PREFIX + DataModelVars.CCSI_DOCUMENT_ASPECT);

				if (parseOutputFile(fileContent, properties) == false)
					throw new Exception("failed in calling parseOutputFile");
				break;

			default:
				break;
			}

			Document document = targetFolder.createDocument(properties, contentStream, versionState);

			statusObject.setSuccess(document.getId());

			return statusObject;

		} catch (FileNotFoundException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.error(e.getLocalizedMessage());
		} catch (IOException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage());
		} catch (CmisContentAlreadyExistsException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document with document name: " + documentName);
		} catch (CmisPermissionDeniedException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document in target folder: " + targetFolder);
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document with document name: " + documentName);
		} finally {
			try {
				if (dis != null) {
					dis.close();
				}

				if (fis != null) {
					fis.close();
				}
			} catch (IOException e) {
				log.error(e.getLocalizedMessage());
				log.error(e.getMessage());
			}
		}

		return statusObject;
	}

	private StatusObject uploadFile(ConnectionClient c, Folder targetFolder, FileInfo uploadFile, String confidence,
			boolean isVersionMajor, String external) {
		StatusObject statusObject = new StatusObject();
		String infoMessage = uploadFile.getDisplayFile() + ":";

		try {
			Session session = c.getAtomSession();

			boolean does_file_exist = doesCmisObjectExist(session,
					targetFolder.getPath() + Common.FWD_SLASH + uploadFile.getDisplayFile());
			if (does_file_exist == true) {
				String objectPath = targetFolder.getPath() + Common.FWD_SLASH + uploadFile.getDisplayFile();
				Document originalDoc = cmisObject2Document(session.getObjectByPath(objectPath));
				CmisObject pwc = null;
				ObjectId checkout_objectID = null;

				if (originalDoc.isVersionSeriesCheckedOut()) {
					String lock_owner = getSinglePropertyAsString(originalDoc.getProperty(DataModelVars.CM_LOCKOWNER));
					String username = c.getUser();
					if (lock_owner == username || username == Common.ADMIN)
						pwc = session.getObject(originalDoc.getId());
					else {
						infoMessage += " failed: no permissions to overwrite locked file " + targetFolder.getPath()
								+ Common.FWD_SLASH + uploadFile.getDisplayFile();
						throw new Exception("You do not have permissions to overwrite locked file: "
								+ targetFolder.getPath() + Common.FWD_SLASH + uploadFile.getDisplayFile());
					}
				} else {
					checkout_objectID = originalDoc.checkOut();
					originalDoc.refresh();
					pwc = session.getObject(checkout_objectID);
				}

				File file = null;
				FileInputStream fis = null;
				DataInputStream dis = null;

				try {
					if (pwc == null) {
						statusObject = createMetadata(targetFolder, uploadFile, confidence, isVersionMajor, external);
						if (statusObject.isOperationSuccessful())
							infoMessage += " Success";
						else
							infoMessage += " Failed with error: " + statusObject.getStatusMessage() + ".";
					} else {
						String dmfChecksum = getSinglePropertyAsString(
								originalDoc.getProperty(DataModelVars.CCSI_CHECKSUM));

						file = new File(uploadFile.getFlenameWPath());
						fis = new FileInputStream(file);
						dis = new DataInputStream(fis);
						byte[] newBytes = new byte[(int) file.length()];
						dis.readFully(newBytes);
						ByteArrayInputStream inputStream = new ByteArrayInputStream(newBytes);
						String uploadCheckSum = this.getChecksum(inputStream);
						if (!uploadCheckSum.equalsIgnoreCase(dmfChecksum)) {
							statusObject = uploadNewMetadata(targetFolder, cmisObject2Document(pwc), uploadFile,
									confidence, isVersionMajor, external);
							if (statusObject.isOperationSuccessful())
								infoMessage += " file exists in " + targetFolder.getPath() + Common.FWD_SLASH
										+ " and its content has been updated.";
							else {
								infoMessage += " Failed with error: " + statusObject.getStatusMessage() + ".";
								cancelCheckOut(originalDoc);
							}
						} else {
							cancelCheckOut(originalDoc);
							infoMessage += " is identical to " + targetFolder.getPath() + Common.FWD_SLASH
									+ uploadFile.getDisplayFile() + ". No action performed.";
							statusObject.setSuccess(originalDoc.getId());
						}
					}
				} catch (Exception e) {
					log.error(e.getLocalizedMessage());
				} finally {
					if (dis != null) {
						dis.close();
					}

					if (fis != null) {
						fis.close();
					}
				}
			} else {
				statusObject = createMetadata(targetFolder, uploadFile, confidence, true, external);
				if (statusObject.isOperationSuccessful())
					infoMessage += " Success";
				else
					infoMessage += " Failed with error: " + statusObject.getStatusMessage() + ".";
			}
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
		}

		statusObject.setDetailsMessage(infoMessage);
		return statusObject;
	}

	private StatusObject createMetadata(Folder targetFolder, FileInfo uploadFile, String confidence,
			boolean isVersionMajor, String external) {
		StatusObject statusObject = new StatusObject();
		MetaDataType eType = uploadFile.getMetaDataType();
		switch (eType) {
		case CONFIG_FILE:
			statusObject = createConfigMetadata(targetFolder, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case INPUT_DATA_FILE:
			statusObject = createInputDataMetadata(targetFolder, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case RESULTS_DATA_FILE:
			statusObject = createResultsDataMetadata(targetFolder, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case EXCEL_DATA_FILE:
			statusObject = createExcelDataMetadata(targetFolder, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case OUTPUT_FILE:
			statusObject = createOutputMetadata(targetFolder, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case UNKNOWN:
			break;
		}
		return statusObject;
	}

	private StatusObject uploadNewMetadata(Folder targetFolder, Document pwc, FileInfo uploadFile, String confidence,
			boolean isVersionMajor, String external) {
		StatusObject statusObject = new StatusObject();
		MetaDataType eType = uploadFile.getMetaDataType();
		switch (eType) {
		case CONFIG_FILE:
			statusObject = uploadNewConfigMetadata(targetFolder, pwc, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case INPUT_DATA_FILE:
			statusObject = uploadNewInputDataMetadata(targetFolder, pwc, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case RESULTS_DATA_FILE:
			statusObject = uploadNewResultsDataMetadata(targetFolder, pwc, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case EXCEL_DATA_FILE:
			statusObject = uploadNewExcelMetadata(targetFolder, pwc, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case OUTPUT_FILE:
			statusObject = uploadNewOutputMetadata(targetFolder, pwc, uploadFile.getDisplayFile(), confidence,
					uploadFile.getFlenameWPath(), isVersionMajor, uploadFile.getDependencies(), external);
			break;

		case UNKNOWN:
			break;
		}

		return statusObject;
	}

	private StatusObject uploadNewConfigMetadata(Folder targetFolder, Document pwc, String documentName,
			String confidence, String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return uploadNewMetaData(targetFolder, pwc, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.CONFIG_FILE);
	}

	private StatusObject uploadNewInputDataMetadata(Folder targetFolder, Document pwc, String documentName,
			String confidence, String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return uploadNewMetaData(targetFolder, pwc, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.INPUT_DATA_FILE);
	}

	private StatusObject uploadNewResultsDataMetadata(Folder targetFolder, Document pwc, String documentName,
			String confidence, String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return uploadNewMetaData(targetFolder, pwc, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.RESULTS_DATA_FILE);
	}

	private StatusObject uploadNewExcelMetadata(Folder targetFolder, Document pwc, String documentName,
			String confidence, String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return uploadNewMetaData(targetFolder, pwc, documentName, EXCEL_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.EXCEL_DATA_FILE);
	}

	private StatusObject uploadNewOutputMetadata(Folder targetFolder, Document pwc, String documentName,
			String confidence, String localPath, boolean isVersionMajor, List<String> parents, String external) {

		return uploadNewMetaData(targetFolder, pwc, documentName, PLAIN_TEXT_MIMETYPE, confidence, isVersionMajor, null,
				localPath, null, null, parents, external, MetaDataType.OUTPUT_FILE);
	}

	private StatusObject uploadNewMetaData(Folder targetFolder, Document pwc, String documentName, String mimeType,
			String confidence, boolean isVersionMajor, ByteArrayInputStream inputStream, String localPath, String title,
			String description, List<String> parents, String external, MetaDataType metaDataType) {

		File file = null;
		FileInputStream fis = null;
		DataInputStream dis = null;
		String sha1 = null;
		StatusObject statusObject = new StatusObject();
		String fileContent = "";
		ObjectId objectId = null;

		try {
			ContentStream contentStream = null;
			Map<String, Object> properties = new HashMap<String, Object>();

			if (inputStream == null) {
				file = new File(localPath);
				fis = new FileInputStream(file);
				dis = new DataInputStream(fis);
				byte[] bytes = new byte[(int) file.length()];
				dis.readFully(bytes);
				inputStream = new ByteArrayInputStream(bytes);
				fileContent = new String(bytes);
				/*
				 * Always set mimetype to plain text to allow alfresco search
				 * file contents, actual mimetype to be set in properties.
				 */

				String test = file.getAbsolutePath();
				if (metaDataType == MetaDataType.EXCEL_DATA_FILE)
					contentStream = new ContentStreamImpl(file.getAbsolutePath(), null, EXCEL_MIMETYPE, inputStream);
				else
					contentStream = new ContentStreamImpl(file.getAbsolutePath(), null, PLAIN_TEXT_MIMETYPE,
							inputStream);
			} else {
				if (metaDataType == MetaDataType.EXCEL_DATA_FILE)
					contentStream = new ContentStreamImpl(file.getAbsolutePath(), null, EXCEL_MIMETYPE, inputStream);
				else
					contentStream = new ContentStreamImpl(documentName, null, PLAIN_TEXT_MIMETYPE, inputStream);
			}

			sha1 = this.getChecksum(inputStream);

			try {
				JSONParser parser = new JSONParser();
				JSONObject jsonObject = (JSONObject) parser.parse(new InputStreamReader(inputStream));
				JSONObject flowsheetObject = (JSONObject) jsonObject.get("flowsheet");

				// Populate nodes list
				ArrayList<String> nodes = new ArrayList<String>();
				for (String topLevelKey : flowsheetObject.keySet()) {
					if (topLevelKey.toLowerCase().equals("nodes")) {
						JSONObject nodeProp = (JSONObject) flowsheetObject.get(topLevelKey);
						for (String key : nodeProp.keySet()) {
							nodes.add(key);
						}
					}
				}

				properties.put(DataModelVars.CCSI_SIM, nodes.toString());

			} catch (JSONParseException e) {
				// Handle non-JSON files if needed
			} catch (Exception e) {

			} finally {
				inputStream.reset();
			}

			properties.put(DataModelVars.CCSI_MIMETYPE, mimeType);
			properties.put(DataModelVars.CCSI_CONFIDENCE, confidence);
			properties.put(DataModelVars.CCSI_CHECKSUM, sha1);

			if (title != null) {
				properties.put(DataModelVars.CM_TITLE, title);
			}

			if (description != null) {
				properties.put(DataModelVars.CM_DESCRIPTION, description);
			}

			if (parents != null && !parents.isEmpty()) {
				properties.put(DataModelVars.CCSI_PARENTS, parents);
			}

			if (external != null) {
				properties.put(DataModelVars.CCSI_EXT_LINK, external);
			}

			switch (metaDataType) {
			case CONFIG_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID, DataModelVars.D_PREFIX + DataModelVars.CCSI_CONFIGFILE
						+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED);

				if (parseConfigFile(fileContent, properties) == false)
					throw new Exception("failed in calling parseConfigFile");
				break;

			case EXCEL_DATA_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID, DataModelVars.D_PREFIX + DataModelVars.CCSI_EXCELDATAFILE
						+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED);

				if (parseExcelDataFile(localPath, properties) == false)
					throw new Exception("failed in calling parseExcelDataFile");
				break;

			case INPUT_DATA_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID, DataModelVars.D_PREFIX + DataModelVars.CCSI_DOCUMENT_V
						+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED);
				break;

			case RESULTS_DATA_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID, DataModelVars.D_PREFIX + DataModelVars.CCSI_TEXTDATAFILE
						+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED);

				if (parseTextDataFile(fileContent, properties) == false)
					throw new Exception("failed in calling parseTextDataFile for results data file");
				break;

			case OUTPUT_FILE:
				properties.put(PropertyIds.OBJECT_TYPE_ID, DataModelVars.D_PREFIX + DataModelVars.CCSI_OUTPUTFILE
						+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED);

				if (parseOutputFile(fileContent, properties) == false)
					throw new Exception("failed in calling parseOutputFile");
				break;

			default:
				break;
			}

			try {
				objectId = pwc.checkIn(isVersionMajor, properties, contentStream, "");
				statusObject.setSuccess(objectId.toString().replace("Object Id: ", ""));
			} catch (Exception e) {
				statusObject.setFailure(e.getLocalizedMessage());
				log.debug(e.getLocalizedMessage() + " Attempted to check in document with name: " + documentName);
			}

			return statusObject;

		} catch (FileNotFoundException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.error(e.getLocalizedMessage());
		} catch (IOException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage());
		} catch (CmisContentAlreadyExistsException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document with document name: " + documentName);
		} catch (CmisPermissionDeniedException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document in target folder: " + targetFolder);
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create document with document name: " + documentName);
		} finally {
			try {
				if (dis != null) {
					dis.close();
				}

				if (fis != null) {
					fis.close();
				}
			} catch (IOException e) {
				log.error(e.getLocalizedMessage());
				log.error(e.getMessage());
			}
		}

		return statusObject;
	}

	private int getSubStringIndex(String[] arrayString, int startIndex, String findString) {
		int len = arrayString.length;

		for (int i = startIndex; i < len; i++) {
			if (arrayString[i].toLowerCase().contains(findString.toLowerCase())) {
				return i;
			}
		}
		return -1;
	}

	private boolean parseConfigFile(String fileContent, Map<String, Object> obj) {
		boolean isSuccess = false;
		String foundString = "";
		int index = -1;

		try {
			String subString[];
			subString = fileContent.split("\n");

			index = getSubStringIndex(subString, 0,
					"# timestep (s) | relative convergence tolerance | absolute convergence tolerance");
			if (index >= 0) {
				foundString = subString[index + 1];
				String[] valueString = foundString.split(" ");
				if (valueString.length != 3)
					throw new Exception(
							"failed in parsing line: timestep (s) | relative convergence tolerance | absolute convergence tolerance");
				obj.put(DataModelVars.CCSI_CONFIGFILE_TIMESTEP, Double.parseDouble(valueString[0]));
				obj.put(DataModelVars.CCSI_CONFIGFILE_RELATIVE_TOLERANCE, Double.parseDouble(valueString[1]));
				obj.put(DataModelVars.CCSI_CONFIGFILE_ABSOLUTE_TOLERANCE, Double.parseDouble(valueString[2]));
			}

			index = getSubStringIndex(subString, 0, "# atmospheric pressure of data (Pa) | sorbent density (kg/m^3)");
			if (index >= 0) {
				foundString = subString[index + 1];
				String[] valueString = foundString.split(" ");
				if (valueString.length != 2)
					throw new Exception(
							"failed in parsing line: atmospheric pressure of data (Pa) | sorbent density (kg/m^3)");
				obj.put(DataModelVars.CCSI_CONFIGFILE_ATMOSPHERIC_PRESSURE, Double.parseDouble(valueString[0]));
				obj.put(DataModelVars.CCSI_CONFIGFILE_SORBENT_DENSITY, Double.parseDouble(valueString[1]));
			}

			index = getSubStringIndex(subString, 0, "# dry case bounds");
			if (index >= 0) {
				int block_index = getSubStringIndex(subString, index, "reaction enthalpy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_LOW_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_HIGH_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_LOW_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_HIGH_REACTION_ENTHALPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: dry case reaction enthalpy");
				}

				block_index = getSubStringIndex(subString, index, "reaction entropy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_LOW_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_HIGH_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_LOW_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_HIGH_REACTION_ENTROPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: dry case reaction entropy");
				}

				block_index = getSubStringIndex(subString, index, "activation enthalpy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_LOW_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_HIGH_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_LOW_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_HIGH_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: dry case activation enthalpy");
				}

				block_index = getSubStringIndex(subString, index, "base-10 logarithm of preexponential factor");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_LOW_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_HIGH_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_LOW_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_DRY_HIGH_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception(
								"failed in parsing line: dry case base-10 logarithm of preexponential factor");
				}
			}

			index = getSubStringIndex(subString, 0, "# Wat (Water) Case Bounds");
			if (index >= 0) {
				int block_index = getSubStringIndex(subString, index,
						"number of active adsorption sites for unit volume");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_NUMBER_ACTIVEADSORPSITES,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_NUMBER_ACTIVEADSORPSITES,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_NUMBER_ACTIVEADSORPSITES,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_NUMBER_ACTIVEADSORPSITES,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception(
								"failed in parsing line: water case number of active adsorption sites for unit volume");
				}

				block_index = getSubStringIndex(subString, index, "reaction enthalpy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_REACTION_ENTHALPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: water case reaction enthalpy");
				}

				block_index = getSubStringIndex(subString, index, "reaction entropy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_REACTION_ENTROPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: water case reaction entropy");
				}

				block_index = getSubStringIndex(subString, index, "activation enthalpy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: water case activation enthalpy");
				}

				block_index = getSubStringIndex(subString, index, "base-10 logarithm of preexponential factor");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_LOW_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_WAT_HIGH_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception(
								"failed in parsing line: water case base-10 logarithm of preexponential factor");
				}
			}

			index = getSubStringIndex(subString, 0, "# humid case bounds");
			if (index >= 0) {
				int block_index = getSubStringIndex(subString, index, "reaction enthalpy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_LOW_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_HIGH_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_LOW_REACTION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_HIGH_REACTION_ENTHALPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: humid case reaction enthalpy");
				}

				block_index = getSubStringIndex(subString, index, "reaction entropy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_LOW_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_HIGH_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_LOW_REACTION_ENTROPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_HIGH_REACTION_ENTROPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: humid case reaction entropy");
				}

				block_index = getSubStringIndex(subString, index, "activation enthalpy");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_LOW_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_HIGH_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_LOW_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_HIGH_ACTIVATION_ENTHALPY,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception("failed in parsing line: humid case activation enthalpy");
				}

				block_index = getSubStringIndex(subString, index, "base-10 logarithm of preexponential factor");
				if (block_index >= 0) {
					foundString = subString[block_index + 1];
					String[] valueString = foundString.split(" ");
					int numberValues = valueString.length;
					if (numberValues == 1) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_LOW_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_HIGH_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
					} else if (numberValues == 2) {
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_LOW_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[0]));
						obj.put(DataModelVars.CCSI_CONFIGFILE_HUMID_HIGH_PRESEXPONENTIAL_FACTOR,
								Double.parseDouble(valueString[1]));
					} else
						throw new Exception(
								"failed in parsing line: humid case base-10 logarithm of preexponential factor");
				}
			}

			index = getSubStringIndex(subString, 0, "number of PSO agents per CPU node");
			if (index >= 0) {
				foundString = subString[index + 1];
				String[] valueString = foundString.split(" ");
				if (valueString.length != 1)
					throw new Exception("failed in parsing line: number of PSO agents per CPU node");
				obj.put(DataModelVars.CCSI_CONFIGFILE_NUMBER_PSO, Integer.parseInt(valueString[0]));
			}

			isSuccess = true;
		} catch (Exception e) {
			log.debug(e.getLocalizedMessage() + " Failed to parse config file.");
		}

		return isSuccess;
	}

	private boolean parseExcelDataFile(String filename, Map<String, Object> obj) {
		boolean isSuccess = false;

		try {
			/*
			 * FileInputStream fileInputStream = new FileInputStream(new
			 * File(filename)); HSSFWorkbook workbook = new
			 * HSSFWorkbook(fileInputStream); HSSFSheet sheet =
			 * workbook.getSheetAt(0);
			 *
			 * Iterator rows = sheet.rowIterator(); int found = 0; while
			 * (rows.hasNext()) { if (found >= 2) break; HSSFRow row = (HSSFRow)
			 * rows.next(); Iterator cells = row.cellIterator(); String
			 * rowString = ""; while (cells.hasNext()) { HSSFCell cell =
			 * (HSSFCell) cells.next(); rowString = cell.getStringCellValue();
			 *
			 * if (rowString.toLowerCase().contains("operator")) { String[]
			 * valueString = rowString.split(":"); if (valueString.length != 2)
			 * throw new Exception("failed in finding operator.");
			 * valueString[1] = valueString[1].replaceAll("^\\s+|\\s+$", "");
			 * obj.put(DataModelVars.CCSI_EXCELFILE_EXPERIMENTER_NAME,
			 * valueString[1]); found++; }
			 *
			 * if (rowString.toLowerCase().contains("run date")) { String[]
			 * valueString = rowString.split(":"); if (valueString.length != 2)
			 * throw new Exception("failed in finding operator.");
			 * valueString[1] = valueString[1].replaceAll("^\\s+|\\s+$", "");
			 * obj.put(DataModelVars.CCSI_EXCELFILE_EXPERIMENT_DATE,
			 * valueString[1]); found++; } if (found >= 2) break; } }
			 */
			isSuccess = true;
		} catch (Exception e) {
			log.debug(e.getLocalizedMessage() + " Failed to parse config file.");
		} finally {
		}

		return isSuccess;
	}

	private boolean parseTextDataFile(String fileContent, Map<String, Object> obj) {
		boolean isSuccess = false;

		try {
			String subString[];
			subString = fileContent.split("\n");
			int len = subString.length;
			double minCO2Pressure = 0.0;
			double maxCO2Pressure = 0.0;
			double minH2OPressure = 0.0;
			double maxH2OPressure = 0.0;
			double minTemp = 0.0;
			double maxTemp = 0.0;
			double deltaTime = 0.0;
			double durationTime = 0.0;
			double minWeightFraction = 0.0;
			double maxWeightFraction = 0.0;
			String valueString[];

			double CO2Pressure = 0.0;
			double H2OPressure = 0.0;
			double Temp = 0.0;
			double Time = 0.0;
			double WeightFraction = 0.0;
			boolean useTab = false;

			if (subString[1].indexOf("\t") != -1)
				useTab = true;

			for (int i = 1; i < len; i++) {
				if (useTab == true)
					valueString = subString[i].split("\t");
				else
					valueString = subString[i].split(" ");

				if (valueString.length != 6) {
					throw new Exception("failed in parsing line: " + String.valueOf(i + 1));
				}

				CO2Pressure = Double.parseDouble(valueString[0]);
				H2OPressure = Double.parseDouble(valueString[1]);
				Temp = Double.parseDouble(valueString[2]);
				Time = Double.parseDouble(valueString[3]);
				WeightFraction = Double.parseDouble(valueString[5]);

				if (i == 1) {
					minCO2Pressure = CO2Pressure;
					maxCO2Pressure = CO2Pressure;
					minH2OPressure = H2OPressure;
					maxH2OPressure = H2OPressure;
					minTemp = Temp;
					maxTemp = Temp;
					deltaTime = Time;
					durationTime = Time;
					minWeightFraction = WeightFraction;
					maxWeightFraction = WeightFraction;
					continue;
				}

				if (CO2Pressure < minCO2Pressure)
					minCO2Pressure = CO2Pressure;
				if (CO2Pressure > maxCO2Pressure)
					maxCO2Pressure = CO2Pressure;

				if (H2OPressure < minH2OPressure)
					minH2OPressure = H2OPressure;
				if (H2OPressure > maxH2OPressure)
					maxH2OPressure = H2OPressure;

				if (Temp < minTemp)
					minTemp = Temp;
				if (Temp > maxTemp)
					maxTemp = Temp;

				if (i == 2)
					deltaTime = Time - deltaTime;
				else if (i == len - 1)
					durationTime = Time - durationTime;

				if (WeightFraction < minWeightFraction)
					minWeightFraction = WeightFraction;
				if (WeightFraction > maxWeightFraction)
					maxWeightFraction = WeightFraction;
			}

			obj.put(DataModelVars.CCSI_DATAFILE_MIN_CO2, minCO2Pressure);
			obj.put(DataModelVars.CCSI_DATAFILE_MAX_CO2, maxCO2Pressure);
			obj.put(DataModelVars.CCSI_DATAFILE_MIN_H2O, minH2OPressure);
			obj.put(DataModelVars.CCSI_DATAFILE_MAX_H2O, maxH2OPressure);
			obj.put(DataModelVars.CCSI_DATAFILE_MIN_TEMP, minTemp);
			obj.put(DataModelVars.CCSI_DATAFILE_MAX_TEMP, maxTemp);
			obj.put(DataModelVars.CCSI_DATAFILE_TIME_DURATION, durationTime);
			obj.put(DataModelVars.CCSI_DATAFILE_TIME_STEP, deltaTime);

			isSuccess = true;
		} catch (Exception e) {
			log.debug(e.getLocalizedMessage() + " Failed to parse config file.");
		} finally {
		}

		return isSuccess;
	}

	private boolean setOutputProperties(String paramName, String valueString, int index, Map<String, Object> obj) {
		if (paramName.equalsIgnoreCase("dh_kap1")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DH_KAP1, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("ds_kap1")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DS_KAP1, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("dh_k1")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DH_K1, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("zeta_k1")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_ZETA_K1, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("dh_kaph")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DH_KAPH, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("ds_kaph")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DS_KAPH, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("dh_kh")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DH_KH, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("zeta_kh")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_ZETA_KH, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("dh_kap2")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DH_HAP2, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("ds_kap2")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DS_KAP2, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("dh_k2")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_DH_K2, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("zeta_k2")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_ZETA_K2, Double.parseDouble(valueString));
			return true;
		}
		if (paramName.equalsIgnoreCase("nv")) {
			obj.put(DataModelVars.CCSI_OUTPUTFILE_NV, Double.parseDouble(valueString));
			return true;
		}

		return false;
	}

	private boolean parseOutputFile(String fileContent, Map<String, Object> obj) {
		boolean isSuccess = false;
		String foundString = "";
		int index = -1;

		try {
			String subString[];
			subString = fileContent.split("\n");

			foundString = subString[1];
			int numberOfParams = 0;
			String[] valueString;
			ArrayList<String> arrayParameter = new ArrayList<String>();
			if (!foundString.isEmpty()) {
				valueString = foundString.split("\\|");
				numberOfParams = valueString.length;
				obj.put(DataModelVars.CCSI_OUTPUTFILE_NUMBEROFPARAMS, numberOfParams);

				for (index = 0; index < numberOfParams; index++) {
					String parameter = valueString[index];
					parameter = parameter.trim();
					arrayParameter.add(parameter);
				}
			} else {
				numberOfParams = 0;
				obj.put(DataModelVars.CCSI_OUTPUTFILE_NUMBEROFPARAMS, numberOfParams);
			}

			foundString = "";
			int numberOfLines = subString.length;
			for (index = subString.length - 1; index >= 0; index--) {
				if (!subString[index].startsWith("[")
						&& !subString[index].equalsIgnoreCase("The Final Parameters are as Follows:")) {
					foundString = subString[index];
					break;
				}
			}

			if (!foundString.isEmpty()) {
				valueString = foundString.split(" ");
				if (valueString.length != 3)
					throw new Exception("Failed to parse Number of iterations, Min. Cost, and Max. Cost");
				obj.put(DataModelVars.CCSI_OUTPUTFILE_NUMBEROFITERATIONS, Integer.parseInt(valueString[0]));
				obj.put(DataModelVars.CCSI_OUTPUTFILE_MIN_COST, Double.parseDouble(valueString[1]));
				obj.put(DataModelVars.CCSI_OUTPUTFILE_MAX_COST, Double.parseDouble(valueString[2]));
			}

			if (numberOfParams == 0)
				return true;

			foundString = subString[numberOfLines - 1];
			int startIndex = foundString.lastIndexOf("(") + 1;
			int endIndex = foundString.indexOf(")");
			foundString = foundString.substring(startIndex, endIndex);
			valueString = foundString.split(",");
			if (valueString.length > 0) {
				for (index = 0; index < valueString.length; index++)
					setOutputProperties(arrayParameter.get(index), valueString[index], index, obj);
			}

			/*
			 * obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM1,
			 * Double.parseDouble(valueString[0])); if ( valueString.length > 1
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM2,
			 * Double.parseDouble(valueString[1])); if ( valueString.length > 2
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM3,
			 * Double.parseDouble(valueString[2])); if ( valueString.length > 3
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM4,
			 * Double.parseDouble(valueString[3])); if ( valueString.length > 4
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM5,
			 * Double.parseDouble(valueString[4])); if ( valueString.length > 5
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM6,
			 * Double.parseDouble(valueString[5])); if ( valueString.length > 6
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM7,
			 * Double.parseDouble(valueString[6])); if ( valueString.length > 7
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM8,
			 * Double.parseDouble(valueString[7])); if ( valueString.length > 8
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM9,
			 * Double.parseDouble(valueString[8])); if ( valueString.length > 9
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM10,
			 * Double.parseDouble(valueString[9])); if ( valueString.length > 10
			 * ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM11,
			 * Double.parseDouble(valueString[10])); if ( valueString.length >
			 * 11 ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM12,
			 * Double.parseDouble(valueString[11])); if ( valueString.length >
			 * 12 ) { obj.put(DataModelVars.CCSI_OUTPUTFILE_PARAM13,
			 * Double.parseDouble(valueString[12])); } } } } } } } } } } } }
			 *
			 * }
			 */

			isSuccess = true;
		} catch (Exception e) {
			log.debug(e.getLocalizedMessage() + " Failed to parse config file.");
		} finally {
		}

		return isSuccess;
	}

	@Override
	public void deleteDocument(Document d, boolean isDeleteAllVersions) {
		d.delete(isDeleteAllVersions);
	}

	@Override
	public void deleteFolder(Folder f) {
		f.delete();
	}

	@Override
	public StatusObject checkOutDocument(String targetPath, Document document) {
		return checkOutDocument(targetPath, document, null);
	}

	@Override
	public StatusObject checkOutDocument(String targetPath, Document document, String targetDocumentName) {
		StatusObject statusObject = new StatusObject();

		try {
			ObjectId checkOutId = document.checkOut();
			if (targetPath != null) {
				statusObject = downloadDocument(document, targetPath, targetDocumentName);
			} else {
				statusObject.setSuccess(checkOutId.toString());
			}
		} catch (Exception e) {
			log.error(e.getLocalizedMessage());
		}

		return statusObject;
	}

	@Override
	public StatusObject updateFolderProperties(Folder folder, String folderName, String description,
			boolean isFixedForm) {
		StatusObject statusObject = new StatusObject();

		Map<String, Object> properties = new HashMap<String, Object>();

		properties.put(PropertyIds.OBJECT_TYPE_ID, DataModelVars.F_PREFIX + DataModelVars.CCSI_FOLDER
				+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED);

		if (folderName != null) {
			properties.put(PropertyIds.NAME, folderName);
		}

		if (description != null) {
			properties.put(DataModelVars.CM_DESCRIPTION, description);
		}

		properties.put(DataModelVars.CCSI_FIXED_FORM, isFixedForm);

		try {
			CmisObject cmisObject = folder.updateProperties(properties);
			statusObject.setSuccess(cmisObject.getId().toString().replace("Object Id: ", ""));
		} catch (CmisContentAlreadyExistsException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to update folder with folder name: " + folderName);
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to update folder with folder name: " + folderName);
		}

		return statusObject;
	}

	@Override
	public StatusObject updateDocumentProperties(Document document, String documentName, String title,
			String description, String mimeType, String confidence, List<String> parents, String external,
			String version_requirements) {
		StatusObject statusObject = new StatusObject();

		Map<String, Object> properties = new HashMap<String, Object>();
		properties.put(PropertyIds.OBJECT_TYPE_ID,
				DataModelVars.CCSI_DOCUMENT + Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED
						+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_AUTHOR);

		if (documentName != null) {
			properties.put(PropertyIds.NAME, documentName);
		}

		if (title != null) {
			properties.put(DataModelVars.CM_TITLE, title);
		}

		if (description != null) {
			properties.put(DataModelVars.CM_DESCRIPTION, description);
		}

		properties.put(DataModelVars.CCSI_MIMETYPE, mimeType);
		properties.put(DataModelVars.CCSI_CONFIDENCE, confidence);
		properties.put(DataModelVars.CCSI_CHECKSUM, document.getPropertyValue(DataModelVars.CCSI_CHECKSUM));

		if (parents != null) {
			properties.put(DataModelVars.CCSI_PARENTS, parents);
		}

		if (external != null) {
			properties.put(DataModelVars.CCSI_EXT_LINK, external);
		}

		if (version_requirements != null) {
			properties.put(DataModelVars.CCSI_VER_REQ, version_requirements);
		}

		try {
			CmisObject cmisObject = document.updateProperties(properties);
			statusObject.setSuccess(cmisObject.getId().toString().replace("Object Id: ", ""));
		} catch (CmisContentAlreadyExistsException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to update document with document name: " + documentName);
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to update document with document name: " + documentName);
		}

		return statusObject;
	}

	@Override
	public StatusObject uploadNewDocumentVersion(Folder targetFolder, Document pwc, String localPath, String mimeType,
			String confidence, boolean isVersionMajor, String checkInComment, String external,
			String version_requirements) {
		return uploadNewDocumentVersion(targetFolder, pwc, localPath, mimeType, confidence, isVersionMajor,
				checkInComment, null, null, null, null, external, version_requirements);
	}

	@Override
	public StatusObject uploadNewDocumentVersion(Folder targetFolder, Document pwc, String documentName,
			String mimeType, String confidence, boolean isVersionMajor, String checkInComment,
			ByteArrayInputStream inputStream, String title, String description, List<String> parents, String external,
			String version_requirements) {
		StatusObject statusObject = new StatusObject();
		ContentStream contentStream = null;
		ObjectId objectId = null;
		Map<String, Object> properties = new HashMap<String, Object>();
		String sha1 = null;
		if (inputStream == null) {
			File file = new File(documentName);

			byte[] bytes = new byte[(int) file.length()];
			inputStream = new ByteArrayInputStream(bytes);

			sha1 = this.getChecksum(inputStream);
			contentStream = new ContentStreamImpl(file.getAbsolutePath(), null, PLAIN_TEXT_MIMETYPE, inputStream);

		} else {

			sha1 = this.getChecksum(inputStream);
			contentStream = new ContentStreamImpl(documentName, null, PLAIN_TEXT_MIMETYPE, inputStream);
		}

		properties.put(PropertyIds.OBJECT_TYPE_ID, DataModelVars.D_PREFIX + DataModelVars.CCSI_DOCUMENT_V
				+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED);

		properties.put(DataModelVars.CCSI_MIMETYPE, mimeType);
		properties.put(DataModelVars.CCSI_CONFIDENCE, confidence);
		properties.put(DataModelVars.CCSI_CHECKSUM, sha1);

		if (title != null) {
			properties.put(DataModelVars.CM_TITLE, title);
		}

		if (description != null) {
			properties.put(DataModelVars.CM_DESCRIPTION, description);
		}

		if (parents != null && !parents.isEmpty()) {
			properties.put(DataModelVars.CCSI_PARENTS, parents);
		}

		if (external != null) {
			properties.put(DataModelVars.CCSI_EXT_LINK, external);
		}
		
		if (version_requirements != null) {
			properties.put(DataModelVars.CCSI_VER_REQ, external);
		}

		try {
			objectId = pwc.checkIn(isVersionMajor, properties, contentStream, checkInComment);
			statusObject.setSuccess(objectId.toString().replace("Object Id: ", ""));
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to check in document with name: " + documentName);
		}
		return statusObject;
	}

	@Override
	public StatusObject createFolder(Folder targetFolder, String folderName) {
		return createFolder(targetFolder, folderName, null, false);
	}

	@Override
	public StatusObject createFolder(Folder targetFolder, String folderName, String description, boolean isFixedForm) {
		Map<String, Object> properties = new HashMap<String, Object>();
		StatusObject statusObject = new StatusObject();

		properties.put(PropertyIds.OBJECT_TYPE_ID, DataModelVars.F_PREFIX + DataModelVars.CCSI_FOLDER
				+ Common.COMMA_SEPARATOR + DataModelVars.P_PREFIX + DataModelVars.CM_TITLED);

		properties.put(PropertyIds.NAME, folderName);

		if (description != null) {
			properties.put(DataModelVars.CM_DESCRIPTION, description);
		}

		properties.put(DataModelVars.CCSI_FIXED_FORM, isFixedForm);

		try {
			Folder newFolder = targetFolder.createFolder(properties);
			statusObject.setSuccess(newFolder.getId());
		} catch (CmisContentAlreadyExistsException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create folder with filename: " + folderName);
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.debug(e.getLocalizedMessage() + " Attempted to create folder with filename: " + folderName);
		}
		return statusObject;
	}

	@Override
	public Folder getHighLevelFolder(Session atomSession, String highLevelFolderName) {
		Folder rootFolder = atomSession.getRootFolder();

		ItemIterable<CmisObject> iterable = rootFolder.getChildren();
		for (CmisObject i : iterable) {
			if (i.getName().equals(highLevelFolderName)) {
				return this.cmisObject2Folder(i);
			}
		}

		return null;
	}

	@Override
	public Folder getUserRootFolder(Session atomSession, String userRootFolderName) {
		Folder userHomes = getHighLevelFolder(atomSession, DataFolderMap.USER_HOMES);
		for (CmisObject i : userHomes.getChildren()) {
			if (i.getName().equals(userRootFolderName)) {
				return this.cmisObject2Folder(i);
			}
		}
		return null;
	}

	/*
	 * Get target folder that belongs to a high level folder. If the target
	 * folder does not exist, a copy will be created.
	 */

	public Folder getTargetFolderInParentFolder(Session atomSession, String parentFolderPath, String targetFolderName,
			boolean isCreateIfNotPresent) {
		return getTargetFolderInParentFolder(atomSession, parentFolderPath, targetFolderName, "", "",
				isCreateIfNotPresent);
	}

	public Folder getTargetFolderInParentFolder(Session atomSession, String parentFolderPath, String targetFolderName,
			String targetFolderTitle, String targetFolderDescription, boolean isCreateIfNotPresent) {
		Folder targetFolder = null;
		CmisObject cmisObject = null;
		StatusObject createFolderStatus = null;

		DataOperationsImpl d = new DataOperationsImpl();

		cmisObject = atomSession.getObjectByPath(parentFolderPath);

		if (cmisObject != null) {
			targetFolder = cmisObject2Folder(cmisObject);
			try {
				cmisObject = atomSession.getObjectByPath(parentFolderPath + Common.FWD_SLASH + targetFolderName);
			} catch (CmisObjectNotFoundException e) {
				if (isCreateIfNotPresent) {
					createFolderStatus = d.createFolder(targetFolder, targetFolderName, targetFolderDescription, false);
					cmisObject = atomSession.getObject(createFolderStatus.getDataObjectID());

				} else {
					return null;
				}
			}

			targetFolder = this.cmisObject2Folder(cmisObject);
		}

		return targetFolder;
	}

	public byte[] getContentsFromURL(String url, String userName, String password) {
		HttpURLConnection conn = null;
		BufferedReader reader = null;

		byte[] contents = null;
		String authString = userName + Common.COLON + password;
		byte[] authEncBytes = Base64.getEncoder().encode(authString.getBytes());
		String authStringEnc = new String(authEncBytes);
		try {

			conn = (HttpURLConnection) new URL(url).openConnection();
			conn.setRequestProperty("Authorization", "Basic " + authStringEnc);

			reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), Common.CHARSET));

			StringBuffer buffer = new StringBuffer();

			for (String line; (line = reader.readLine()) != null;) {
				buffer.append(line);
			}
			contents = String.valueOf(buffer).getBytes();

		} catch (IOException e) {
			log.error("IO Exception detected: " + e.getMessage());
		} finally {
			if (reader != null)
				try {
					reader.close();
					conn.disconnect();
				} catch (IOException ignore) {
				}
		}

		return contents;
	}

	public boolean isDocumentDiff(Document documentName1, Document documentName2) {

		ContentStream contentStream1 = documentName1.getContentStream();
		ContentStream contentStream2 = documentName2.getContentStream();
		InputStream stream1 = contentStream1.getStream();
		InputStream stream2 = contentStream2.getStream();
		try {
			int c1 = stream1.read();
			int c2 = stream2.read();
			while (c1 > 0 && c2 > 0) {
				if (c1 != c2) {
					stream1.close();
					stream2.close();
					return true;
				}

				c1 = stream1.read();
				c2 = stream2.read();
			}

			stream1.close();
			stream2.close();
			return false;

		} catch (IOException e) {
			log.error("IO Exception detected: " + e.getMessage());
			return true;
		} catch (Exception e) {
			log.error("Exception detected: " + e.getMessage());
			return true;
		}
	}

	@Override
	public byte[] getDocumentContentsAsByteArray(InputStream inputStream, int blockLength) {
		byte[] bytes = new byte[blockLength];
		try {
			int sizeRead = inputStream.read(bytes, 0, blockLength);
			return Arrays.copyOfRange(bytes, 0, sizeRead);
		} catch (IOException e) {
			e.printStackTrace();
			return bytes;
		} catch (Exception e) {
			e.printStackTrace();
			return bytes;
		}
	}

	@Override
	public StatusObject downloadDocument(Document document, String targetPath) {
		return downloadDocument(document, targetPath, null);
	}

	@Override
	public StatusObject downloadDocument(Document document, String targetPath, String targetDocumentName) {
		ContentStream contentStream = document.getContentStream();
		File outputFile = null;
		FileOutputStream fos = null;
		InputStream inputStream = null;
		StatusObject statusObject = new StatusObject();

		if (targetDocumentName != null) {
			outputFile = new File(targetPath + targetDocumentName);
		} else {
			outputFile = new File(
					targetPath + contentStream.getFileName() + Common.VERSION_SEPARATOR + document.getVersionLabel());
		}

		try {
			fos = new FileOutputStream(outputFile);
			inputStream = contentStream.getStream();
			for (int read = inputStream.read(); read != -1; read = inputStream.read()) {
				fos.write(read);
			}

			statusObject.setSuccess(document.getId());

		} catch (FileNotFoundException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.error(e.getLocalizedMessage());
		} catch (IOException e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.error(e.getLocalizedMessage());
		} catch (Exception e) {
			statusObject.setFailure(e.getLocalizedMessage());
			log.error(e.getLocalizedMessage());
		} finally {
			try {
				if (fos != null) {
					fos.flush();
					fos.close();
				}

				if (inputStream != null) {
					inputStream.close();
				}
			} catch (IOException e) {
				log.error(e.getLocalizedMessage());
			}
		}

		return statusObject;
	}

	@Override
	public boolean cancelCheckOut(Document document) {

		String versionSeriesCheckedOutId = document.getVersionSeriesCheckedOutId();
		if (versionSeriesCheckedOutId == null) {
			log.debug("Attempting to delete non-private working copy");
			return false;
		} else {
			document.cancelCheckOut();
			return true;
		}

	}

	@Override
	public File downloadZipFolder(Session atomSession, List<String> ids) {
		File zip = null;
		final String PREFIX = "dmf_tmp";
		final String ZIP_EXT = ".zip";

		try {
			if (ids != null && !ids.isEmpty()) {
				// Create zip file in java.io.tmpdir
				zip = File.createTempFile(PREFIX, ZIP_EXT);
				FileOutputStream stream = new FileOutputStream(zip);
				CheckedOutputStream checksumOutputStream = new CheckedOutputStream(stream, new Adler32());
				BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(checksumOutputStream);
				ZipOutputStream zipOutputStream = new ZipOutputStream(bufferedOutputStream);
				zipOutputStream.setMethod(ZipOutputStream.DEFLATED);
				zipOutputStream.setLevel(Deflater.BEST_COMPRESSION);

				try {
					for (String id : ids) {
						CmisObject cmisObject = atomSession.getObject(id);
						appendCMISObject2Zip(atomSession, cmisObject, zipOutputStream);
					}
				} catch (Exception e) {
					log.error("Exception: " + e.getLocalizedMessage());
				} finally {
					zipOutputStream.close();
					bufferedOutputStream.close();
					checksumOutputStream.close();
					stream.close();

					if (ids.size() > 0) {
						return zip;
					}
				}
			}
		} catch (Exception e) {
			log.error("Exception:" + e.getLocalizedMessage());
		} finally {
			if (zip != null) {
				zip.deleteOnExit();
			}
		}
		return null;
	}

	private void appendCMISObject2Zip(Session atomSession, CmisObject cmisObject, ZipOutputStream zipOutputStream) {
		appendCMISObject2Zip(atomSession, cmisObject, zipOutputStream, "");
	}

	private void appendCMISObject2Zip(Session atomSession, CmisObject cmisObject, ZipOutputStream zipOutputStream,
			String zipPath) {
		String cmisObjectName = cmisObject.getName();
		InputStream inputStream = null;
		try {
			if (cmisObject.getBaseTypeId() == BaseTypeId.CMIS_DOCUMENT) {
				Document document = cmisObject2Document(cmisObject);
				ContentStream contentStream = document.getContentStream();
				if (contentStream == null) {
					log.error("Failed to read content stream from document: " + cmisObjectName);
				} else {
					inputStream = contentStream.getStream();
					String path = (zipPath.isEmpty() ? "" : zipPath + '/') + cmisObjectName;
					zipOutputStream.putNextEntry(new ZipEntry(path));
					byte[] buffer = new byte[1024]; // Doesn't need to be 1024.
					int nBytes = 0;
					do {
						zipOutputStream.write(buffer, 0, nBytes);
						nBytes = inputStream.read(buffer, 0, buffer.length);
					} while (nBytes > 0);

					inputStream.close();
					zipOutputStream.closeEntry();
				}

			} else if (cmisObject.getBaseTypeId() == BaseTypeId.CMIS_FOLDER) {
				Folder folder = cmisObject2Folder(cmisObject);
				ItemIterable<CmisObject> children = folder.getChildren();

				if (children.getTotalNumItems() > 0) {
					for (CmisObject child : children) {
						String path = (zipPath.isEmpty() ? "" : zipPath + '/') + cmisObjectName;
						appendCMISObject2Zip(atomSession, child, zipOutputStream, path);
					}
				} else {

					String path = (zipPath.isEmpty() ? "" : zipPath + '/') + cmisObjectName + '/';
					zipOutputStream.putNextEntry(new ZipEntry(path));
					zipOutputStream.closeEntry();
				}
			} else {
				log.error("Unsupported CMIS object type: " + cmisObject.getBaseTypeId());
			}

		} catch (IOException e) {
			log.error("IOException: " + e.getLocalizedMessage());
		} finally {
			if (inputStream != null) {
				try {
					inputStream.close();
				} catch (IOException e) {
					log.error("IOException: " + e.getLocalizedMessage());
				}
			}
		}
	}

	@Override
	public String getChecksum(ByteArrayInputStream inputStream) {
		byte[] sha1 = null;

		try {
			MessageDigest md = MessageDigest.getInstance("SHA1");
			DigestInputStream dis = new DigestInputStream(inputStream, md);
			while (dis.available() > 0)
				dis.read();
			sha1 = md.digest();
			// necessary, otherwise contentStream won't be
			// able to read any data
			inputStream.reset();
		} catch (Exception e) {
			log.error(e.getLocalizedMessage());
		}

		StringBuilder hexSHA1 = new StringBuilder();
		for (byte b : sha1) {
			hexSHA1.append(String.format("%02x", b));
		}
		return hexSHA1.toString();
	}

	@Override
	public String getSinglePropertyAsString(Property<?> property) {
		if (property != null && property.getFirstValue() != null) {
			return property.getFirstValue().toString();
		} else {
			return null;
		}
	}

	@Override
	public String[] getVersionHistoryLabels(Session atomSession, CmisObject cmisObject) {
		Document document = this.cmisObject2Document(cmisObject);
		OperationContext operationContext = new OperationContextImpl();
		operationContext.setFilterString(DataModelVars.CMIS_VERSION_LABEL);
		operationContext.setIncludeAcls(false);
		operationContext.setIncludePathSegments(false);
		operationContext.setIncludeAllowableActions(false);
		operationContext.setIncludePolicies(false);
		operationContext.setIncludeRelationships(IncludeRelationships.NONE);
		List<Document> versions = document.getAllVersions(operationContext);

		String[] versionLabels = new String[versions.size()];
		for (int i = 0; i < versions.size(); i++) {
			versionLabels[i] = versions.get(i).getVersionLabel();
		}
		return versionLabels;
	}

	@Override
	public boolean doesCmisObjectExist(Session atomSession, String path) {
		try {
			atomSession.getObjectByPath(path);
			return true;
		} catch (Exception e) {
			return false;
		}
	}

}
