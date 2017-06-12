import package_info

def writeHelpFiles():
	tpm = package_info.getThirdPartyInfo()
	with open("html/thirdPartyInfoTemplate.html", 'r') as f:
		template = f.read()
	for key, item in tpm.iteritems():
		newhtml = template
		newhtml = newhtml.replace("PKG_NAME", key, 1)
		newhtml = newhtml.replace("PKG_VERSION", item["version"], 1)
		newhtml = newhtml.replace("PKG_COPYRIGHT", item["copyright"], 1)
		newhtml = newhtml.replace("PKG_WEB", item["url"], 2)
		newhtml = newhtml.replace("PKG_DOWNLOAD", item["url_source"], 2)
		newhtml = newhtml.replace("PKG_SUMMARY", item["summary"], 1)
		lic = item["license"]
		lic = lic.replace("\n", "<br>")
		newhtml = newhtml.replace("PKG_LICENSE", lic, 1)

		with open("html/"+key+"_info.html", 'w') as f:
			f.write(newhtml)
			
	pkgs = sorted( tpm.keys(), key=lambda s: s.lower() )
	with open("html/thirdPartyListTemplate.html", 'r') as f:
		template = f.read()
	lines = []
	for p in pkgs:
		fn = p+"_info.html"
		lines.append("<p><h3><a href=\"{}\">{}</a></h3>{}</p>\n".format(fn, p, " ver " + tpm[p]["version"] + "; " + tpm[p]["copyright"]))
	newhtml = template.replace("PKG_LIST", "".join(lines), 1)
	with open("html/thirdPartyDependencies.html", 'w') as f:
		f.write(newhtml)

if __name__ == '__main__':		
	writeHelpFiles()
