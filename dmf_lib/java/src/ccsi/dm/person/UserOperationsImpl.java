package ccsi.dm.person;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.Authenticator;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.PasswordAuthentication;
import java.net.URL;
import java.net.URLConnection;
import java.util.Map;

import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import ccsi.dm.common.Common;
import ccsi.dm.connection.ConnectionClient;
import ccsi.dm.json.JSONProcessor;

public class UserOperationsImpl implements UserOperations {

	private static Logger log = LoggerFactory.getLogger(UserOperationsImpl.class.getName());

	private final String ALFRESCO_PERSON_REST_URL = "/alfresco/service/api/people/";

	@Override
	public boolean deleteUser(ConnectionClient c, String personName) {
		boolean isSuccessStatusCode = false;
		HttpURLConnection httpConnection = null;
		try {
			URL deleteUserURL = new URL(
					c.getAlfrescoURL() + ALFRESCO_PERSON_REST_URL + personName + "?alf_ticket=" + c.getLoginTicket());
			URLConnection connection = deleteUserURL.openConnection();
			Authenticator.setDefault(new Authenticator() {
				protected PasswordAuthentication getPasswordAuthentication() {
					return new PasswordAuthentication(c.getUser(), c.getPassword().toCharArray());
				}
			});

			httpConnection = (HttpURLConnection) connection;
			httpConnection.setDoOutput(true);
			httpConnection.setRequestProperty("Accept-Charset", Common.CHARSET);
			httpConnection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
			httpConnection.setRequestMethod("DELETE");
			httpConnection.connect();

			int statusCode = httpConnection.getResponseCode();
			isSuccessStatusCode = (statusCode == HttpURLConnection.HTTP_OK);

			if (isSuccessStatusCode) {
				log.debug("Delete user is successful.");
			} else {
				log.error("Delete user is unsuccessful, status: " + statusCode);
			}
		} catch (MalformedURLException e) {
			log.error("MalformedURLException: " + e.getLocalizedMessage());
		} catch (IOException e) {
			log.error("IOException: " + e.getLocalizedMessage());
		} finally {
			if (httpConnection != null) {
				httpConnection.disconnect();
			}
		}
		return isSuccessStatusCode;
	}

	@Override
	public boolean doesUserExist(ConnectionClient c, String userName) {
		boolean isSuccessStatusCode = false;
		HttpURLConnection httpConnection = null;

		try {
			URL getPersonURL = new URL(
					c.getAlfrescoURL() + ALFRESCO_PERSON_REST_URL + userName + "?alf_ticket=" + c.getLoginTicket());
			URLConnection connection = getPersonURL.openConnection();
			Authenticator.setDefault(new Authenticator() {
				protected PasswordAuthentication getPasswordAuthentication() {
					return new PasswordAuthentication(c.getUser(), c.getPassword().toCharArray());
				}
			});

			httpConnection = (HttpURLConnection) connection;
			httpConnection.setRequestProperty("Accept-Charset", Common.CHARSET);
			httpConnection.connect();

			int statusCode = httpConnection.getResponseCode();
			isSuccessStatusCode = (statusCode == HttpURLConnection.HTTP_OK);
			if (isSuccessStatusCode) {
				log.debug("Get person is successful.");
			} else {
				log.error("Get person unsuccessful with status: " + statusCode);
			}
		} catch (MalformedURLException e) {
			log.error("MalformedURLException: " + e.getLocalizedMessage());
		} catch (IOException e) {
			log.error("IOException: " + e.getLocalizedMessage());
		} finally {
			if (httpConnection != null) {
				httpConnection.disconnect();
			}
		}

		return isSuccessStatusCode;
	}

	@Override
	public boolean createUser(ConnectionClient c, String userName, String firstName, String lastName, String email) {
		return createUser(c, userName, firstName, lastName, email, null, null, null);
	}

	@Override
	public boolean createUser(ConnectionClient c, String userName, String firstName, String lastName, String email,
			String password, String title, String organization) {

		boolean isSuccessStatusCode = false;
		HttpURLConnection httpConnection = null;

		JSONObject userDetails = new JSONObject();
		if (userName != null)
			userDetails.put("userName", userName);

		if (firstName != null)
			userDetails.put("firstName", firstName);

		if (lastName != null)
			userDetails.put("lastName", lastName);

		if (email != null)
			userDetails.put("email", email);

		if (password != null)
			userDetails.put("password", password);

		if (title != null)
			userDetails.put("title", title);

		if (organization != null)
			userDetails.put("organisation", organization);

		try {
			URL addUserURL = new URL(
					c.getAlfrescoURL() + ALFRESCO_PERSON_REST_URL.substring(0, ALFRESCO_PERSON_REST_URL.length() - 1)
							+ "?alf_ticket=" + c.getLoginTicket());
			URLConnection connection = addUserURL.openConnection();
			Authenticator.setDefault(new Authenticator() {
				protected PasswordAuthentication getPasswordAuthentication() {
					return new PasswordAuthentication(c.getUser(), c.getPassword().toCharArray());
				}
			});
			
			httpConnection = (HttpURLConnection) connection;
			httpConnection.setDoOutput(true);
			httpConnection.setRequestProperty("Accept-Charset", Common.CHARSET);
			httpConnection.setRequestProperty("Content-Type", "application/json; charset=" + Common.CHARSET);
			httpConnection.setRequestMethod("POST");

			OutputStreamWriter writer = new OutputStreamWriter(httpConnection.getOutputStream(), Common.CHARSET);
			writer.write(userDetails.toString());
			writer.flush();
			writer.close();

			int statusCode = httpConnection.getResponseCode();
			isSuccessStatusCode = (statusCode == HttpURLConnection.HTTP_OK);
			if (isSuccessStatusCode) {
				log.debug("Person create is successful.");
			}
		} catch (MalformedURLException e) {
			log.error("MalformedURLException: " + e.getLocalizedMessage());
		} catch (IOException e) {
			log.error("IOException: " + e.getLocalizedMessage());
		} finally {
			if (httpConnection != null) {
				httpConnection.disconnect();
			}
		}

		return isSuccessStatusCode;
	}

	@Override
	public boolean updateUserPassword(ConnectionClient c, String key) {
		// TODO Auto-generated method stub
		return false;
	}

	@Override
	public Map<String, Object> getUser(ConnectionClient c, String userName) {

		boolean isSuccessStatusCode = false;
		HttpURLConnection httpConnection = null;

		try {
			URL getUserURL = new URL(c.getAlfrescoURL() + ALFRESCO_PERSON_REST_URL + userName + "?groups=true");
			URLConnection connection = getUserURL.openConnection();
			Authenticator.setDefault(new Authenticator() {
				protected PasswordAuthentication getPasswordAuthentication() {
					return new PasswordAuthentication(c.getUser(), c.getPassword().toCharArray());
				}
			});

			httpConnection = (HttpURLConnection) connection;
			httpConnection.setRequestProperty("Accept-Charset", Common.CHARSET);
			httpConnection.connect();

			int statusCode = httpConnection.getResponseCode();
			isSuccessStatusCode = (statusCode == HttpURLConnection.HTTP_OK);
			if (isSuccessStatusCode) {
				log.debug("GetUser is successful.");
				BufferedReader bufferedReader = new BufferedReader(
						new InputStreamReader(httpConnection.getInputStream()));
				StringBuilder responseBuilder = new StringBuilder();

				String line;
				while ((line = bufferedReader.readLine()) != null) {
					responseBuilder.append(line + '\n');
				}

				JSONObject json = new JSONObject(responseBuilder.toString());
				return (new JSONProcessor()).jsonObject2Map(json);
			} else {
				log.error("GetUser is not successful, status: " + statusCode);
			}
		} catch (MalformedURLException e) {
			log.error("MalformedURLException: " + e.getLocalizedMessage());
		} catch (IOException e) {
			log.error("IOException: " + e.getLocalizedMessage());
		} finally {
			if (httpConnection != null) {
				httpConnection.disconnect();
			}
		}
		return null;
	}
}