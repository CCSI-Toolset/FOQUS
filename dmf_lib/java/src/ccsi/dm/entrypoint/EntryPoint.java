package ccsi.dm.entrypoint;

import ccsi.dm.accesscontrol.AccessControlImpl;
import ccsi.dm.connection.ConnectionClient;
import ccsi.dm.data.DataOperationsImpl;
import ccsi.dm.person.UserOperationsImpl;
import py4j.GatewayServer;
import py4j.Py4JNetworkException;

public class EntryPoint {

	private AccessControlImpl a = null;
	private DataOperationsImpl d = null;
	private UserOperationsImpl u = null;

	public EntryPoint() {
		a = new AccessControlImpl();
		d = new DataOperationsImpl();
		u = new UserOperationsImpl();
	}

	public ConnectionClient getConnectionClient() {
		return new ConnectionClient();
	}

	public ConnectionClient getConnectionClient(String alfrescoRepoProp) {
		return new ConnectionClient(alfrescoRepoProp);
	}

	public ConnectionClient getConnectionClient(String user, String password) {
		return new ConnectionClient(user, password);
	}

	public ConnectionClient getConnectionClient(String alfrescoRepoProp,
			String user, String password) {
		return new ConnectionClient(alfrescoRepoProp, user, password);
	}

	public AccessControlImpl getAccessControlImpl() {
		return a;
	}
	
	public DataOperationsImpl getDataOperationsImpl() {
		return d;
	}

	public UserOperationsImpl getUserOperationsImpl() {
		return u;
	}

	public static void main(String[] args) {

		GatewayServer gatewayServer = new GatewayServer(new EntryPoint());

		try {
			gatewayServer.start();
		} catch (Py4JNetworkException e) {
			// If server has been started or port is used, shutdown gateway.
			// Otherwise, gateway remains initialized.
			gatewayServer.shutdown();
		}
	}
}
