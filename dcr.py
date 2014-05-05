from lxml import html
from urllib import request
import re
import json
import time
from selenium import webdriver
from datetime import datetime

def isoFromString (date_string):
	#December 31, 2010
	parsed_date = time.strptime(date_string, "%B %d, %Y ")
	return datetime.date(datetime.fromtimestamp(time.mktime(parsed_date))).isoformat()

# ---------------------------------------------------------------
# get_DCRS_by_year:	This returns metadata for the DC Register
#			issues for a given year 
# ---------------------------------------------------------------
def get_DCRs_by_year (issue_year):
	# Note, the years are from 2009 to 2014
	data = []
	url = "http://dcregs.dc.gov/Gateway/IssueList.aspx?IssueYear=" + str(issue_year)
	issue_page_url = request.urlopen(url)
	issue_page = html.parse(issue_page_url)
	issues = issue_page.xpath('//div[@id="ctl00_ContentPlaceHolder_divYearIssue"]//li/a')
	for issue in issues:
		issue_url = issue.xpath("@href")[0]
		issue_id = re.split("=", issue_url)[1]
		try:
			issue_full = issue.xpath("text()")[0].split("-")
			issue_date = isoFromString(issue_full[0])
			issue_vn = issue_full[1].split("/")
			issue_vol = issue_vn[0].split(" ")[2]
			issue_no = issue_vn[1]
			data.append({
				"id":issue_id,
				"date":issue_date,
				"url":issue_url,
				"volume":issue_vol,
				"number":issue_no,
				"pdf_url": get_issue_PDF(issue_id)
				})

		except:
			continue
	return data

# ---------------------------------------------------------------
# get_issue_PDF: 	This returns the url for a particular 
#			issue of the Register 
# ---------------------------------------------------------------
def get_issue_PDF (issue_id):
	url = "http://dcregs.dc.gov/Gateway/IssueHome.aspx?IssueId=" + str(issue_id)
	issue_page = html.parse(request.urlopen(url))
	issue_url = issue_page.xpath("//a[@id='ctl00_ContentPlaceHolder_hlRegisterFile']/@href")[0]
	return issue_url

# ---------------------------------------------------------------
# get_issue_notices:	This is intended to get the notices for
#			each issue of the Register, but it's
#			dependent on getting the notices for each
#			action (see get_action_notices), 
#			and that currently doesn't work. 
# ---------------------------------------------------------------
def get_issue_notices (issue_id):
	data = []
	url = "http://dcregs.dc.gov/Gateway/IssueHome.aspx?IssueId=" + str(issue_id)
	issue_page = html.parse(request.urlopen(url))
	issue_council_actions = issue_page.xpath("//table[@id='ctl00_ContentPlaceHolder_dlCouncilIssueList']//div[@class='issuestext']//a[1]")
	for action in issue_council_actions:
		action_url = action.xpath("@href")[0].replace("..","http://dcregs.dc.gov")
		action_description = action.xpath("text()")[0]
		data.append({
			"action_url":action_url, 
			"action_description":action_description,
			"action_items":get_action_notices(action_url)
		})
	issue_executive_actions = issue_page.xpath("//table[@id='ctl00_ContentPlaceHolder_dlAgencyIssueList']//div[@class='issuestext']//a[1]")
	for action in issue_executive_actions:
		action_url = action.xpath("@href")[0].replace("..","http://dcregs.dc.gov")
		action_description = action.xpath("text()")[0]
		data.append({
			"action_url":action_url, 
			"action_description":action_description,
			"action_items":get_action_notices(action_url)
		})
	
	return data

# ---------------------------------------------------------------
# get_action_notices: 	This is supposed to get each notice for
# 			each action, but it's BROKEN!
# ---------------------------------------------------------------
def get_action_notices (action_url):
	# Ok. So. Here's the approach. There are two main steps. First, you get the metadata for the page that you're on. 
	# Then, you figure out whether there are multiple pages and, if so, you navigate to that page and start again. 

	notice_data = []
	driver = webdriver.PhantomJS()
	driver.get(action_url)

	# Find the total number of records & divide by 15 to calculate the total number of pages
	pages = int(driver.find_element_by_id("ctl00_ContentPlaceHolder_lblCount").text) / 15
	i = 0
	out = driver.find_element_by_id("ctl00_ContentPlaceHolder_gvNotice").get_attribute("outerHTML")
	notice_data.extend(get_json_of_notices(out))

	# Loop through each page to get all of the rows
	while i < pages:
		i = 1 + i
		driver.execute_script("__doPostBack('ctl00$ContentPlaceHolder$gvNotice','Page$" + str(i + 1) + "')")
		time.sleep(3)
		out = driver.find_element_by_id("ctl00_ContentPlaceHolder_gvNotice").get_attribute("outerHTML")
		notice_data.extend(get_json_of_notices(out))

	driver.quit

	return notice_data

def get_json_of_notices (table):
	data = []
	table = html.document_fromstring(table)
	rows = table.xpath("//tr")
	for row in rows:
		cells = row.xpath("td")
		if len(cells) > 2:
			if cells[0].text_content().strip() != "1":
				if len(cells) == 5:
					data.append({
						"notice_id": cells[0].text_content().strip(),
						"notice_title":cells[2].text_content().strip()
					})
				else:
					data.append({
						"notice_id": cells[0].text_content().strip(),
						"notice_title":cells[1].text_content().strip()
					})
	return data


# ---------------------------------------------------------------
# create_DCR_json:	This generates a huge JSON file of the 
#			metadata for DC Register issues 
# ---------------------------------------------------------------
def create_DCR_json ():
	out_data = []
	issue_year = 2009
	while (issue_year < 2015):
		out_data.append({
			"year":issue_year,
			"issues":get_DCRs_by_year(issue_year)
			})
		issue_year = issue_year + 1
	return out_data

#print(json.dumps(create_DCR_json(), indent=2))

def write_issue_to_file (issue_no):
	with open("issues/" + issue_no + ".json", 'w') as f:
	  	json.dump(get_issue_notices(issue_no), f, indent=2)

f = open('dcr_issue_metadata.json','r')
f = json.load(f)[1]
for issue in f["issues"]:
	write_issue_to_file(issue["id"])
	print("Issue " + issue["id"] + ": written to file")

#print(json.dumps(get_issue_notices("432"),indent=2))