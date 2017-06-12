from urllib2 import urlopen
from urllib2 import Request
from base64 import encodestring


class AlfrescoServiceAdaptor():
    MIMETYPE_DESCRIPTION_LINK = "/alfresco/service/api/mimetypes/descriptions"
    PEOPLE_LIST = "/alfresco/service/api/people"

    def getAlfrescoMimetypes(self, url):
        url = str(url) + AlfrescoServiceAdaptor.MIMETYPE_DESCRIPTION_LINK
        response = urlopen(url)
        content = response.read()
        status_code = response.getcode()
        response.close()
        return content, status_code

    def getAlfrescoUserList(self, url, user, pw):
        url = str(url) + AlfrescoServiceAdaptor.PEOPLE_LIST
        request = Request(url)
        base64string = encodestring('%s:%s' % (user, pw)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        response = urlopen(request)
        content = response.read()
        status_code = response.getcode()
        response.close()
        return content, status_code
