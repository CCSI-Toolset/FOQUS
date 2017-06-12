package ccsi.dm.accesscontrol;

import org.apache.chemistry.opencmis.client.api.Session;

/* Alfresco specific permissions control */

public interface AccessControl {
	public boolean addPermissions(Session s, String uid, String oid, Role role);
	public boolean deletePermissions(Session s, String uid, String oid);
}
