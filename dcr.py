from lxml import html
import urllib2
import re
import json
import time
from datetime import datetime
import dcr_notice

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
	issue_page_url = urllib2.urlopen(url)
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

		except Exception, e:
			print e
			continue
	return data

# ---------------------------------------------------------------
# get_issue_PDF: 	This returns the url for a particular 
#			issue of the Register 
# ---------------------------------------------------------------
def get_issue_PDF (issue_id):
	url = "http://dcregs.dc.gov/Gateway/IssueHome.aspx?IssueId=" + str(issue_id)
	issue_page = html.parse(urllib2.urlopen(url))
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
	issue_page = html.parse(urllib2.urlopen(url))
	issue_council_actions = issue_page.xpath("//table[@id='ctl00_ContentPlaceHolder_dlCouncilIssueList']//div[@class='issuestext']//a[1]")
	for action in issue_council_actions:
		action_url = action.xpath("@href")[0]
		action_description = action.xpath("text()")[0]
		data.append({
			"action_url":action_url, 
			"action_description":action_description,
			"action_items":get_action_notices(action_url)
		})
	issue_executive_actions = issue_page.xpath("//table[@id='ctl00_ContentPlaceHolder_dlAgencyIssueList']//div[@class='issuestext']//a[1]")
	for action in issue_executive_actions:
		action_url = action.xpath("@href")[0]
		action_description = action.xpath("text()")[0]
		data.append({
			"action_url":action_url, 
			"action_description":action_description
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
	next_page = 1
	while (next_page != null):
		notice_page = html.parse(urllib2.urlopen(action_url))
		notice_actions = notice_page.xpath("//table[@id]='ctl00_ContentPlaceHolder_gvNotice'")

		# You actually need to click through to get to the metadata page

		notice_data.append({
			"notice_title": notice_title,
			"notice_text": notice_text,
			"notice_url": notice_url
		})
	return notice_data

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

print json.dumps(create_DCR_json(), indent=2)
