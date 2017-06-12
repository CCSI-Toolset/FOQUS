package ccsi.dm.person;

import java.util.Map;

import ccsi.dm.connection.ConnectionClient;

public interface UserOperations {
	public boolean createUser(ConnectionClient c, String userName, String firstName,
			String lastName, String email);
	public boolean createUser(ConnectionClient c, String userName, String firstName,
			String lastName, String email, String password, String title,
			String organization);	
	public boolean doesUserExist(ConnectionClient c, String userName);
	public boolean deleteUser(ConnectionClient c, String userName);
	public boolean updateUserPassword(ConnectionClient c, String key);
	public Map<String, Object> getUser(ConnectionClient c, String userName);
}
