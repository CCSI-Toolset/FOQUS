package ccsi.dm.connection;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.net.Authenticator;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.PasswordAuthentication;
import java.net.ProtocolException;
import java.net.URL;
import java.net.URLConnection;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.cert.CertificateException;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.apache.chemistry.opencmis.client.api.Repository;
import org.apache.chemistry.opencmis.client.api.Session;
import org.apache.chemistry.opencmis.client.api.SessionFactory;
import org.apache.chemistry.opencmis.client.runtime.SessionFactoryImpl;
import org.apache.chemistry.opencmis.commons.SessionParameter;
import org.apache.chemistry.opencmis.commons.enums.BindingType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.xml.sax.SAXException;

import ccsi.dm.common.Common;

public class ConnectionClient {

	private final static String DEFAULT_ALFRESCO_REPO_CONFIG = "../config/alfresco-repo.properties";

	private final String IP_ADDRESS = "IP_ADDRESS";
	private final String PORT = "PORT";
	private final String PROTOCOL = "PROTOCOL";

	private final String ALFRESCO_ATOMPUB_URL = "alfresco_atompub_url";

	private final String AUTH_HTTP_BASIC = "auth_http_basic";
	private final String COOKIES = "cookies";
	private final String REPOSITORY_ID = "repositoryId";
	private final String USER = "alf_user";
	private final String PASSWORD = "alf_key";
	private final String TICKET = "ticket";

	private static Logger log = LoggerFactory.getLogger(ConnectionClient.class.getName());
	private InputStream input;
	private Properties repoProp = new Properties();
	private Session session = null;
	private static String loginTicket = null;

	static {
		javax.net.ssl.HttpsURLConnection.setDefaultHostnameVerifier(new javax.net.ssl.HostnameVerifier() {

			public boolean verify(String hostname, javax.net.ssl.SSLSession sslSession) {
				try {
					KeyStore ks = KeyStore.getInstance(KeyStore.getDefaultType());
					InputStream ksStream = new FileInputStream(
							System.getProperty("java.home") + "/lib/security/jssecacerts");

					char[] password = "changeit".toCharArray();
					ks.load(ksStream, password);
					Enumeration<String> aliases = ks.aliases();
					while (aliases.hasMoreElements()) {
						String nextElement = aliases.nextElement();
						if (nextElement.startsWith(hostname)) {
							return true;
						}
					}
				} catch (KeyStoreException e) {
					log.error("KeyStoreException: " + e.getLocalizedMessage());
				} catch (NoSuchAlgorithmException e) {
					log.error("NoSuchAlgorithmException: " + e.getLocalizedMessage());
				} catch (CertificateException e) {
					log.error("CertificateException: " + e.getLocalizedMessage());
				} catch (IOException e) {
					log.error("IOException: " + e.getLocalizedMessage());
				}
				return false;
			}
		});
	}

	public ConnectionClient() {
		this(null);
	}

	public ConnectionClient(String userName, String password) {
		this(null, userName, password);
	}

	public ConnectionClient(String alfrescoRepoProp, String userName, String password) {
		this(alfrescoRepoProp);
		repoProp.setProperty(USER, userName);
		repoProp.setProperty(PASSWORD, password);
	}

	public ConnectionClient(String alfrescoRepoProp) {
		try {

			if (alfrescoRepoProp != null)
				input = new FileInputStream(alfrescoRepoProp);
			else {
				URL location = this.getClass().getProtectionDomain().getCodeSource().getLocation();
				String path = location.toString().replaceFirst(location.getProtocol() + ":", "");
				input = new FileInputStream(path + DEFAULT_ALFRESCO_REPO_CONFIG);
			}
			repoProp.load(input);
			input.close();

		} catch (FileNotFoundException e) {
			log.error("FileNotFoundException: " + e.getLocalizedMessage());
		} catch (IOException e) {
			log.error("IOException: " + e.getLocalizedMessage());
		} finally {
			if (input != null) {
				try {
					input.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
	}

	public String getUser() {
		return repoProp.getProperty(USER);
	}

	public String getPassword() {
		return repoProp.getProperty(PASSWORD);
	}

	public String getAlfrescoServerAddress() {
		return repoProp.getProperty(IP_ADDRESS);
	}

	public String getProtocol() {
		return repoProp.getProperty(PROTOCOL);
	}

	public String getAlfrescoServerPort() {
		return repoProp.getProperty(PORT);
	}

	public String getLoginTicket() {
		return loginTicket;
	}

	public String getAlfrescoURL() {
		return this.getProtocol() + this.getAlfrescoServerAddress() + Common.COLON + this.getAlfrescoServerPort();
	}

	public void createAtomSession() {
		long time1 = System.currentTimeMillis();
		SessionFactory sessionFactory = SessionFactoryImpl.newInstance();
		Map<String, String> parameter = new HashMap<String, String>();

		parameter.put(SessionParameter.USER, this.getUser());
		parameter.put(SessionParameter.PASSWORD, this.getPassword());
		parameter.put(SessionParameter.BINDING_TYPE, BindingType.ATOMPUB.value());
		parameter.put(SessionParameter.ATOMPUB_URL, this.getProtocol() + this.getAlfrescoServerAddress() + Common.COLON
				+ this.getAlfrescoServerPort() + repoProp.getProperty(ALFRESCO_ATOMPUB_URL));
		parameter.put(SessionParameter.AUTH_HTTP_BASIC, repoProp.getProperty(AUTH_HTTP_BASIC));
		parameter.put(SessionParameter.COOKIES, repoProp.getProperty(COOKIES));
		parameter.put(SessionParameter.OBJECT_FACTORY_CLASS, "org.alfresco.cmis.client.impl.AlfrescoObjectFactoryImpl");

		// Unlike other CMIS systems, Alfresco supports only one repository
		List<Repository> repositories = sessionFactory.getRepositories(parameter);
		this.session = repositories.get(0).createSession();

		log.debug("Got a connection to repository: " + repoProp.getProperty(REPOSITORY_ID));

		long time2 = System.currentTimeMillis();
		long difftime = time2 - time1;

		log.debug("Time taken to connect atom session: " + difftime + " ms.");
	}

	public Session getAtomSession() {
		return this.session;
	}

	/* Code for connecting to perform Alfresco specific operations */
	public boolean login() {
		boolean isSuccessStatusCode = false;
		HttpURLConnection httpConnection = null;
		try {
			URL loginURL = new URL(
					this.getProtocol() + this.getAlfrescoServerAddress() + Common.COLON + this.getAlfrescoServerPort()
							+ "/alfresco/service/api/login?" + "u=" + this.getUser() + "&pw=" + this.getPassword());
			URLConnection connection = loginURL.openConnection();
			Authenticator.setDefault(new Authenticator() {
				protected PasswordAuthentication getPasswordAuthentication() {
					return new PasswordAuthentication(getUser(), getPassword().toCharArray());
				}
			});

			httpConnection = (HttpURLConnection) connection;
			httpConnection.setRequestProperty("Accept-Charset", Common.CHARSET);
			httpConnection.connect();

			int statusCode = httpConnection.getResponseCode();
			isSuccessStatusCode = (statusCode == HttpURLConnection.HTTP_OK);
			if (isSuccessStatusCode) {
				DocumentBuilderFactory builderFactory = DocumentBuilderFactory.newInstance();
				DocumentBuilder builder = builderFactory.newDocumentBuilder();
				Document document = builder.parse(httpConnection.getInputStream());
				Element rootElement = document.getDocumentElement();
				if (rootElement.getNodeName().equals(TICKET)) {
					loginTicket = rootElement.getTextContent();
				}
				log.debug("Login is successful, ticket: " + this.getLoginTicket());
			} else {
				log.error("Login is not successful, status: " + statusCode);
			}
		} catch (MalformedURLException e) {
			log.error("MalformedURLException: " + e.getLocalizedMessage());
		} catch (IOException e) {
			log.error("IOException: " + e.getLocalizedMessage());
		} catch (ParserConfigurationException e) {
			log.error("ParserConfigurationException: " + e.getLocalizedMessage());
		} catch (SAXException e) {
			log.error("SAXException: " + e.getLocalizedMessage());
		} finally {
			if (httpConnection != null) {
				httpConnection.disconnect();
			}
		}
		return isSuccessStatusCode;

	}

	/* Code for connecting to perform Alfresco specific operations */
	public boolean logout() {
		boolean isSuccessStatusCode = false;
		HttpURLConnection httpConnection = null;
		try {
			URL validateURL = new URL(this.getProtocol() + this.getAlfrescoServerAddress() + Common.COLON
					+ this.getAlfrescoServerPort() + "/alfresco/service/api/login/ticket/" + this.getLoginTicket());
			URLConnection connection = validateURL.openConnection();
			connection.setRequestProperty("Accept-Charset", Common.CHARSET);
			Authenticator.setDefault(new Authenticator() {
				protected PasswordAuthentication getPasswordAuthentication() {
					return new PasswordAuthentication(getUser(), getPassword().toCharArray());
				}
			});

			httpConnection = (HttpURLConnection) connection;
			httpConnection.setDoOutput(true);
			httpConnection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
			httpConnection.setRequestMethod("DELETE");
			httpConnection.connect();

			int statusCode = httpConnection.getResponseCode();
			isSuccessStatusCode = (statusCode == HttpURLConnection.HTTP_OK);

			if (isSuccessStatusCode) {
				log.debug("Logout is successful.");
			} else {
				log.error("Logout is not successful, status: " + statusCode);
			}
		} catch (MalformedURLException e) {
			log.error("MalformedURLException: " + e.getLocalizedMessage());
		} catch (ProtocolException e) {
			log.error("ProtocolException: " + e.getLocalizedMessage());
		} catch (IOException e) {
			log.error("IOException: " + e.getLocalizedMessage());
		} finally {
			if (httpConnection != null) {
				httpConnection.disconnect();
			}
		}
		return isSuccessStatusCode;
	}

	public boolean validateTicket(String ticket) {
		boolean isSuccessStatusCode = false;
		HttpURLConnection httpConnection = null;
		try {
			URL validateURL = new URL(this.getProtocol() + this.getAlfrescoServerAddress() + Common.COLON
					+ this.getAlfrescoServerPort() + "/alfresco/service/api/login/ticket/" + ticket);
			URLConnection connection = validateURL.openConnection();
			Authenticator.setDefault(new Authenticator() {
				protected PasswordAuthentication getPasswordAuthentication() {
					return new PasswordAuthentication(getUser(), getPassword().toCharArray());
				}
			});

			httpConnection = (HttpURLConnection) connection;
			httpConnection.setRequestProperty("Accept-Charset", Common.CHARSET);
			httpConnection.connect();

			isSuccessStatusCode = (httpConnection.getResponseCode() == HttpURLConnection.HTTP_OK);
			if (isSuccessStatusCode) {
				log.debug("Ticket validation successful.");
			} else {
				log.error("Ticket validation is not successful, ticket: " + ticket);
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
}
