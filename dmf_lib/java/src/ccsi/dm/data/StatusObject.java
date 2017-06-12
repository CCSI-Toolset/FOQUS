package ccsi.dm.data;

public class StatusObject {
	private boolean isSuccess;
	private String dataObjectID;
	private String statusMessage;
	private String dataObjectVersion;
	private String detailsMessage;

	private final String SUCCESS = "Success";

	public boolean isOperationSuccessful() {
		return this.isSuccess;
	}

	public String getDataObjectID() {
		return this.dataObjectID;
	}

	public String getDataObjectVersion() {
		return this.dataObjectVersion;
	}

	public String getStatusMessage() {
		return this.statusMessage;
	}
	
	public String getDetailsMessage() {
		return this.detailsMessage;
	}
	/*
	 * If successful, return dataObjectID with success status message.
	 */
	public void setSuccess(String dataObjectID) {
		this.setDataObjectID(dataObjectID);
		this.extractDataObjectVersion();
		this.setIsSuccess(true);
		this.setStatusMessage(this.SUCCESS);
	}

	/*
	 * If failure occurs, return object with dataObjectID = null and return
	 * status message of error.
	 */
	public void setFailure(String statusMessage) {
		this.setDataObjectID(null);
		this.setIsSuccess(false);
		this.setStatusMessage(statusMessage);
	}

	public void setDetailsMessage(String detailsMessage) {
		this.detailsMessage = detailsMessage;
	}
	
	private void setDataObjectID(String dataObjectID) {
		this.dataObjectID = dataObjectID;
	}

	private void setIsSuccess(boolean isSuccess) {
		this.isSuccess = isSuccess;
	}

	private void setStatusMessage(String statusMessage) {
		this.statusMessage = statusMessage;
	}
	
	private void setDataObjectVersion(String dataObjectVersion) {
		this.dataObjectVersion = dataObjectVersion;
	}

	private void extractDataObjectVersion() {
		String[] split = this.dataObjectID.split(";");
		if (split.length > 1) {
			this.setDataObjectVersion(split[split.length-1]);
		} else {
			this.setDataObjectVersion(null);
		}
	}
}
