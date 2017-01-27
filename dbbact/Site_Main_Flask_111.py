from flask import Blueprint, request
import json
import requests
from utils import debug, getdoc

Site_Main_Flask_Obj = Blueprint('Site_Main_Flask_Obj', __name__, template_folder='templates')


#scbd_server_address = 'http://amnonim.webfactional.com/scdb_main'
scbd_server_address = '127.0.0.:5001'


@Site_Main_Flask_Obj.route('/site/test_html', methods=['POST', 'GET'])
def test_html():
    """
    Title: Test Html
    URL: site/test_html
    Method: GET
    """

    webPage = "<html><body><center>this is supercool db!</center></body></html>"

    cfunc = test_html
    if request.method == 'POST':
        return(getdoc(cfunc))

    return webPage


@Site_Main_Flask_Obj.route('/main', methods=['POST', 'GET'])
def main_html():
    """
    Title: Test Html
    URL: site/main_html
    Method: GET
    """
    return "test2222"
    webPage = ""
    webPage += "<html>"
    webPage += "<title>Seqeunce Search</title>"
    webPage += "<body>"
    webPage += "<center>"
    webPage += "<div style='border-radius: 5px; background-color: #f2f2f2; padding: 20px;'>"
    webPage += "<form action='search_results' method='post'><h1>Sequence Search</h1><br>"
    webPage += "<input value='tacggagggtgcgagcgttaatcggaataactgggcgtaaagggcacgcaggcggtgacttaagtgaggtgtgaaagccccgggcttaacctgggaattgcatttcatactgggtcgctagagtactttagggaggggtagaattccacg' style='width: 100%; font-size:20px; height: 30px; margin-bottom: 20px;' type='text' name='sequence'><br>"
    webPage += "<input style='height: 40px; width: 140px; font-size:20px;' type='submit'>"
    webPage += "</form></div>"
    webPage += "</center></body></html>"

    cfunc = test_html
    if request.method == 'POST':
        return(getdoc(cfunc))

    return webPage


@Site_Main_Flask_Obj.route('/search_results', methods=['POST'])
def search_results():
    """
    Title: Search results page
    URL: site/search_results
    Method: POST
    """

    return "test1111"
    sequence = request.form['sequence']

    style = "<style>table {margin:40px; border-collapse: collapse; width: 100%;} th, td {text-align: left; padding: 8px;}tr:nth-child(even){background-color: #f2f2f2}th {background-color: #4CAF50;color: white; margin-top:100px;}</style>"

    webPage = ""
    webPage += "<html>"
    webPage += "<title>Seqeunce Search</title>"
    webPage += "<head>" + style + "</head>"
    webPage += "<body>Search results for sequence:" + sequence + "<br>"

    rdata = {}
    rdata['sequence'] = sequence
    httpRes = requests.get(scbd_server_address + '/sequences/get_annotations', json=rdata)

    if httpRes.status_code != requests.codes.ok:
        debug(6, "Error code:" + str(httpRes.status_code))
        webPage += "Failed to get annotations for the given sequence"
    else:
        jsonResponse = httpRes.json()
        webPage += "<table>"
        webPage += "<col width='10%'>"
        webPage += "<col width='30%'>"
        webPage += "<col width='60%'>"
        webPage += "<tr>"
        webPage += "<th>Expirment id</th>"
        webPage += "<th>Description</th>"
        webPage += "<th>Details</th>"
        webPage += "</tr>"
        strDetails = ""
        for dataRow in jsonResponse.get('annotations'):
            webPage += "<tr>"
            webPage += "<td><a href=exp_info/" + str(dataRow.get('expid', 'not found')) + ">" + str(dataRow.get('expid', 'not found')) + "</a></td>"
            cdesc = getannotationstrings(dataRow)
            # webPage += "<td>" + str(dataRow.get('description','not found')) + "</td>"
            webPage += "<td>" + cdesc + "</td>"
            #webPage += "<td>" + str(dataRow) + "</td>"
            strDetails = ''
            for detailesRow in dataRow.get('details'):
                strDetails += str(detailesRow)
            webPage += "<td>" + str(strDetails) + "</td>"
            webPage += "</tr>"
        webPage += "</table>"
    webPage += "</body>"
    webPage += "</html>"

    return webPage


def getannotationstrings(cann):
    """
    get a nice string summary of a curation

    input:
    cann : dict from /sequences/get_annotations (one from the list)
    output:
    cdesc : str
            a short summary of each annotation
    """
    cdesc = ''
    if cann['description']:
        cdesc += cann['description'] + ' ('
    if cann['annotationtype'] == 'diffexp':
        chigh = []
        clow = []
        call = []
        for cdet in cann['details']:
            if cdet[0] == 'all':
                call.append(cdet[1])
                continue
            if cdet[0] == 'low':
                clow.append(cdet[1])
                continue
            if cdet[0] == 'high':
                chigh.append(cdet[1])
                continue
        cdesc += ' high in '
        for cval in chigh:
            cdesc += cval + ' '
        cdesc += ' compared to '
        for cval in clow:
            cdesc += cval + ' '
        cdesc += ' in '
        for cval in call:
            cdesc += cval + ' '
    elif cann['annotationtype'] == 'isa':
        cdesc += ' is a '
        for cdet in cann['details']:
            cdesc += 'cdet,'
    elif cann['annotationtype'] == 'contamination':
        cdesc += 'contamination'
    else:
        cdesc += cann['annotationtype'] + ' '
        for cdet in cann['details']:
            cdesc = cdesc + ' ' + cdet[1] + ','
    return cdesc


@Site_Main_Flask_Obj.route('/exp_info/<int:expid>')
def getexperimentinfo(expid):
    """
    get the information about a given study dataid
    input:
    dataid : int
            The dataid on the study (DataID field)

    output:
    info : list of (str,str,str)
            list of tuples for each entry in the study:
            type,value,descstring about dataid
            empty if dataid not found
    """
    rdata = {}
    rdata['expId'] = expid
    res = requests.get(scbd_server_address + '/experiments/get_details', json=rdata)
    if res.status_code == 200:
        outstr = ''
        for cres in res.json()['details']:
            outstr += cres[0] + ':' + cres[1] + '<br>'
        # details=res.json()['details']
        return outstr
    return []
