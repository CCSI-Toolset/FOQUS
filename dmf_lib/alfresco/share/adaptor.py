from urllib import urlencode
from urllib2 import build_opener
from urllib2 import HTTPCookieProcessor
from cookielib import CookieJar


class AlfrescoShareAdaptor():
    LOGIN_LINK = "/share/page/dologin"
    SEARCH_LINK = "/share/proxy/alfresco/slingshot/search?repo=true&term="

    def alfrescoShareLogin(self, url, username, password):
        url = str(url) + AlfrescoShareAdaptor.LOGIN_LINK
        cookie_jar = CookieJar()
        data = dict(username=username, password=password)
        data_encoded = urlencode(data)
        opener = build_opener(HTTPCookieProcessor(cookie_jar))
        response = opener.open(url, data_encoded)
        response.close()
        return cookie_jar

    def alfrescoShareFullTextSearch(self, url, term, cookiejar):
        url = str(url) + AlfrescoShareAdaptor.SEARCH_LINK + str(term)
        opener = build_opener(HTTPCookieProcessor(cookiejar))
        response = opener.open(url)
        text = response.read()
        status_code = response.getcode()
        response.close()
        return text, status_code

    def getAlfrescoSharePreview(self, url, cookiejar):
        url = str(url)
        opener = build_opener(HTTPCookieProcessor(cookiejar))
        response = opener.open(url)
        # content is an image
        content = response.read()
        status_code = response.getcode()
        response.close()
        return content, status_code
