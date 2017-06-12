package ccsi.dm.data;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.InputStream;
import java.util.List;

import org.apache.chemistry.opencmis.client.api.CmisObject;
import org.apache.chemistry.opencmis.client.api.Document;
import org.apache.chemistry.opencmis.client.api.Folder;
import org.apache.chemistry.opencmis.client.api.Property;
import org.apache.chemistry.opencmis.client.api.Session;

import ccsi.dm.connection.ConnectionClient;

public interface DataOperations {
	public StatusObject createSorbentFitMetadata(ConnectionClient c, String fileFolder, String confidence,
			boolean isVersionMajor, String external);

	public StatusObject createConfigMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external);

	public StatusObject createConfigMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external);

	public StatusObject createExcelDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external);

	public StatusObject createExcelDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external);

	public StatusObject createInputDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external);

	public StatusObject createInputDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external);

	public StatusObject createResultsDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external);

	public StatusObject createResultsDataMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external);

	public StatusObject createOutputMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, String external);

	public StatusObject createOutputMetadata(Folder targetFolder, String documentName, String confidence,
			String localPath, boolean isVersionMajor, List<String> parents, String external);

	public StatusObject createVersionedDocument(Folder targetFolder, String documentName, String mimeType,
			String confidence, String localPath, boolean isVersionMajor, String external, String version_requirements);

	public StatusObject createVersionedDocument(Folder targetFolder, String documentName, String mimeType,
			String confidence, String localPath, boolean isVersionMajor, String title, String description,
			List<String> parents, String external, String version_requirements);

	public StatusObject createVersionedDocument(Folder targetFolder, String documentName, String mimeType,
			String confidence, ByteArrayInputStream inputStream, boolean isVersionMajor, String title,
			String description, List<String> parents, String external, String version_requirements);

	public StatusObject createDocument(Folder targetFolder, String documentName, String mimeType, String confidence,
			String localPath, String external, String version_requirements);

	public StatusObject createDocument(Folder targetFolder, String documentName, String mimeType, String confidence,
			String localPath, String title, String description, List<String> parents, String external, String version_requirements);

	public StatusObject createDocument(Folder targetFolder, String documentName, String mimeType, String confidence,
			ByteArrayInputStream inputStream, List<String> parents, String external, String version_requirements);

	public void deleteDocument(Document d, boolean isDeleteAllVersions);

	public void deleteFolder(Folder f);

	public StatusObject checkOutDocument(String targetPath, Document document);

	public StatusObject checkOutDocument(String targetPath, Document document, String targetDocumentName);

	/*
	 * CAUTION: Cancelling checkout on a non-private working copy will delete
	 * that copy
	 */
	public boolean cancelCheckOut(Document pwc);

	public StatusObject uploadNewDocumentVersion(Folder targetFolder, Document pwc, String localPath, String mimeType,
			String confidence, boolean isVersionMajor, String checkInComment, String external, String version_requirements);

	public StatusObject uploadNewDocumentVersion(Folder targetFolder, Document pwc, String documentName,
			String mimeType, String confidence, boolean isVersionMajor, String checkInComment,
			ByteArrayInputStream inputStream, String title, String description, List<String> parents, String external, String version_requirements);

	public StatusObject createFolder(Folder targetFolder, String folderName);

	public StatusObject createFolder(Folder targetFolder, String folderName, String description, boolean isFixedForm);

	public byte[] getDocumentContentsAsByteArray(InputStream inputStream, int blockLength);

	public StatusObject downloadDocument(Document document, String targetPath);

	public StatusObject downloadDocument(Document document, String targetPath, String targetDocumentName);

	public StatusObject updateDocumentProperties(Document document, String documentName, String title,
			String description, String mimeType, String confidence, List<String> parents, String external,
			String version_requirements);

	public StatusObject updateFolderProperties(Folder folder, String folderName, String description,
			boolean isFixedForm);

	public Folder getHighLevelFolder(Session atomSession, String highLevelFolderName);

	public Folder getUserRootFolder(Session atomSession, String userRootFolderName);

	public Folder cmisObject2Folder(CmisObject cmisObject);

	public Document cmisObject2Document(CmisObject cmisObject);

	public File downloadZipFolder(Session atomSession, List<String> ids);

	public String getChecksum(ByteArrayInputStream inputStream);

	public String getSinglePropertyAsString(Property<?> property);

	public String[] getVersionHistoryLabels(Session atomSession, CmisObject cmisObject);

	public boolean doesCmisObjectExist(Session atomSession, String path);
}
