import foqus_lib.version.version as ver

def writeHelpFiles():
    #There are 4 main CCSI Packages used by FOQUS
    #
    # 1. FOQUS
    # 2. Turbine Client
    # 3. PSUADE
    # 4. ALAMO
    #
    # For now I'm going to ignore ALAMO and PSUADE they need to be installed separately
    # so I'm not going to worry about including their licenses.
    #
    # read the template for the HTML license files
    with open("html/licenseTemplate.html", 'r') as f:
        template = f.read()
    #Both FOQUS and Turbine are CCSI Testing and Evaluation for now
    with open("../../LICENSE.md", 'r') as f:
        lic = f.read()
    lic = lic.replace("\n", "<br>")
    template2 = template.replace("PKG_LICENSE", lic, 1)
    newhtml = template2.replace("PKG_NAME", "FOQUS")
    newhtml = newhtml.replace("[SOFTWARE NAME & VERSION]", "FOQUS " + str(ver.version), 1)
    
    newhtml = newhtml.replace("PKG_COPYRIGHT", ver.copyright)
    with open("html/foqus_license.html", 'w') as f:
        f.write(newhtml)
    newhtml = template2.replace("PKG_NAME", "Turbine Client")
    newhtml = newhtml.replace("[SOFTWARE NAME & VERSION]", "Turbine Client", 1)
    newhtml = newhtml.replace("PKG_COPYRIGHT", ver.copyright)
    with open("html/turbine_client_license.html", 'w') as f:
        f.write(newhtml)

if __name__ == '__main__':
    writeHelpFiles()
