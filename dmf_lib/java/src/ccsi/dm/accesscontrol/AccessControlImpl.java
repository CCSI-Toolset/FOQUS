package ccsi.dm.accesscontrol;

import java.util.ArrayList;
import java.util.List;

import org.apache.chemistry.opencmis.client.api.CmisObject;
import org.apache.chemistry.opencmis.client.api.OperationContext;
import org.apache.chemistry.opencmis.client.api.Session;
import org.apache.chemistry.opencmis.client.runtime.OperationContextImpl;
import org.apache.chemistry.opencmis.commons.BasicPermissions;
import org.apache.chemistry.opencmis.commons.data.Ace;
import org.apache.chemistry.opencmis.commons.enums.AclPropagation;

public class AccessControlImpl implements AccessControl {

	@Override
	public boolean addPermissions(Session atomSession, String userOrGroupId,
			String cmisObjectId, Role role) {
		OperationContext operationContext = new OperationContextImpl();
		operationContext.setIncludeAcls(true);
		CmisObject cmisObject = atomSession.getObject(cmisObjectId,
				operationContext);
		List<Ace> aces = cmisObject.getAcl().getAces();
		List<String> permissions;
		int ordinal = -1;
		int removalIndex = -1;

		// Check if user or group ID exists in ACE
		for (int i = 0; i < aces.size(); i++) {
			if (aces.get(i).getPrincipalId().contains(userOrGroupId)) {
				removalIndex = i;
				for (String p : aces.get(i).getPermissions()) {
					if (p.contains(Role.Collaborator.name())) {
						ordinal = Role.Collaborator.ordinal();
					} else if (p.contains(Role.Editor.name())) {
						ordinal = Role.Editor.ordinal();
					} else if (p.contains(Role.Consumer.name())) {
						ordinal = Role.Consumer.ordinal();
					} else if (p.contains(Role.Coordinator.name())) {
						ordinal = Role.Coordinator.ordinal();
					} else if (p.contains(Role.Contributor.name())) {
						ordinal = Role.Contributor.ordinal();
					}
				}
				break;
			}
		}

		if (ordinal == role.ordinal()) {
			return true;
		} else {
			if (removalIndex != -1) {
				aces.remove(removalIndex);
			}
			permissions = this.setupPermissions(role, ordinal);
		}

		Ace ace = atomSession.getObjectFactory().createAce(userOrGroupId,
				permissions);

		try {
			if (ordinal != -1) {
				aces.add(ace);
				for (int i = 0; i < aces.size();) {
					if (!aces.get(i).isDirect()) {
						aces.remove(i);
					} else {
						i++;
					}
				}
				this.cleanupPermissions(aces, userOrGroupId);
				cmisObject.setAcl(aces);
			} else {
				List<Ace> newAces = new ArrayList<Ace>();
				newAces.add(ace);
				cmisObject.addAcl(newAces, AclPropagation.REPOSITORYDETERMINED);

				// Alfresco seems to have a bug when adding new permissions to
				// existing set of permissions. This is visible through Alfresco
				// Share, hence cleaning up necessary.
				aces = atomSession.getObject(cmisObjectId, operationContext)
						.getAcl().getAces();				
				this.cleanupPermissions(aces, userOrGroupId);
				cmisObject.setAcl(aces);
			}

			return true;
		} catch (Exception e) {
			System.err.println(e);
			return false;
		}
	}

	@Override
	public boolean deletePermissions(Session atomSession, String userOrGroupId,
			String cmisObjectId) {
		OperationContext operationContext = new OperationContextImpl();
		operationContext.setIncludeAcls(true);
		CmisObject cmisObject = atomSession.getObject(cmisObjectId,
				operationContext);
		List<Ace> aces = cmisObject.getAcl().getAces();
		for (int i = 0; i < aces.size(); i++) {
			if (aces.get(i).getPrincipalId().equals(userOrGroupId)) {
				aces.remove(i);
				break;
			}
		}
		for (int i = 0; i < aces.size();) {
			if (!aces.get(i).isDirect()) {
				aces.remove(i);
			} else {
				i++;
			}
		}
		System.out.println("Aces:" + aces);
		try {
			cmisObject.setAcl(aces);
			// Alfresco seems to have a bug when deleting permissions, which
			// result in system permissions being created. This is visible
			// through Alfresco Share, hence cleaning up necessary.
			aces = atomSession.getObject(cmisObjectId, operationContext)
					.getAcl().getAces();
			this.cleanupPermissions(aces, userOrGroupId);
			cmisObject.setAcl(aces);
			return true;
		} catch (Exception e) {
			System.err.println(e);
			return false;
		}
	}

	private void cleanupPermissions(List<Ace> aces, String user) {
		for (int i = 0; i < aces.size();) {
			if (!aces.get(i).isDirect()) {
				aces.remove(i);
			} else {
				i++;
			}
		}
		
		for (Ace a : aces) {
			List<String> permissions = a.getPermissions();
			permissions
					.remove("{http://www.alfresco.org/model/security/1.0}All.All");
			permissions
					.remove("{http://www.alfresco.org/model/system/1.0}base.Read");
			permissions
					.remove("{http://www.alfresco.org/model/system/1.0}base.Write");
		}
	}

	private List<String> setupPermissions(Role role, int ordinal) {
		List<String> permissions = new ArrayList<String>();
		System.out.println(ordinal);
		permissions.add("{http://www.alfresco.org/model/system/1.0}cmobject."
				+ role.name());
		switch (role) {
		case Editor:
			if (ordinal == Role.Coordinator.ordinal()) {
				permissions.add(BasicPermissions.WRITE);
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.ALL);
			} else if (ordinal == Role.Contributor.ordinal()) {
				permissions.add(BasicPermissions.READ);
			} else if (ordinal == Role.Collaborator.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
			} else if (ordinal == Role.Consumer.ordinal()) {
				permissions.add(BasicPermissions.READ);
			}
			break;
		case Consumer:
			if (ordinal == Role.Editor.ordinal()) {
				permissions.add(BasicPermissions.WRITE);
				permissions.add(BasicPermissions.READ);
			} else if (ordinal == Role.Contributor.ordinal()) {
				permissions.add(BasicPermissions.READ);
			} else if (ordinal == Role.Coordinator.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
				permissions.add(BasicPermissions.ALL);
			} else if (ordinal == Role.Collaborator.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
			}
			break;
		case Collaborator:
			if (ordinal == Role.Consumer.ordinal()) {
				permissions.add(BasicPermissions.READ);
			} else if (ordinal == Role.Coordinator.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
				permissions.add(BasicPermissions.ALL);
			} else if (ordinal == Role.Editor.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
			} else if (ordinal == Role.Contributor.ordinal()) {
				permissions.add(BasicPermissions.READ);
			}
			break;
		case Coordinator:
			if (ordinal == Role.Consumer.ordinal()) {
				permissions.add(BasicPermissions.READ);
			} else if (ordinal == Role.Collaborator.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
			} else if (ordinal == Role.Contributor.ordinal()) {
				permissions.add(BasicPermissions.READ);
			} else if (ordinal == Role.Editor.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
			}
			break;
		case Contributor:
			if (ordinal == Role.Consumer.ordinal()) {
				permissions.add(BasicPermissions.READ);
			} else if (ordinal == Role.Editor.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
			} else if (ordinal == Role.Collaborator.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
			} else if (ordinal == Role.Coordinator.ordinal()) {
				permissions.add(BasicPermissions.READ);
				permissions.add(BasicPermissions.WRITE);
				permissions.add(BasicPermissions.ALL);
			}
			break;
		}
		return permissions;
	}
}
