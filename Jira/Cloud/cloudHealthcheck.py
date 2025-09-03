import requests
from requests.auth import HTTPBasicAuth
import json
import csv
from datetime import datetime
import os
import configfile as cfg

#sys.stdout = open("output.txt", "w+")

startTime = datetime.now()

dir_path = "deliverables"

FolderExist = os.path.exists(dir_path)

if not FolderExist:
   # Create a new directory because it does not exist
   os.makedirs(dir_path)
   print("Folder " + dir_path+ " directory does not exist and has just been created!")

filename = {
    "results"                   : cfg.jira_cloud_instance_name + "_" + "results_" + cfg.timestr + ".csv",
    "jira_projects"             : cfg.jira_cloud_instance_name + "_" + "jira_projects_" + cfg.timestr + ".csv",
    "dashboards_global_list"    : cfg.jira_cloud_instance_name + "_" + "dashboards_global_list_" + cfg.timestr + ".txt",
    "filters_global_list"       : cfg.jira_cloud_instance_name + "_" + "filters_global_list_" + cfg.timestr +".txt",
    "issue_types_usage"         : cfg.jira_cloud_instance_name + "_" + "issue_types_usage_" + cfg.timestr +".csv",
    "workflows_unused"          : cfg.jira_cloud_instance_name + "_" + "unused_workflows_" + cfg.timestr +".csv",
    "screens_unused"            : cfg.jira_cloud_instance_name + "_" + "unused_screens_" + cfg.timestr +".csv",
    "custom_fields_unused"      : cfg.jira_cloud_instance_name + "_" + "unused_custom_fields_" + cfg.timestr +".csv",
    "custom_fields_duplicates"  : cfg.jira_cloud_instance_name + "_" + "custom_fields_duplicates_" + cfg.timestr +".txt",
    "custom_fields_unique"      : cfg.jira_cloud_instance_name + "_" + "custom_fields_unique_" + cfg.timestr +".txt",
    "unused_statuses"           : cfg.jira_cloud_instance_name + "_" + "unused_statuses_" + cfg.timestr +".csv",
    "statuses_unique"           : cfg.jira_cloud_instance_name + "_" + "statuses_unique_" + cfg.timestr +".txt",
}

auth = HTTPBasicAuth(cfg.auth["user"], cfg.auth["token"])
auth_confluence = HTTPBasicAuth(cfg.auth_confluence["user"], cfg.auth_confluence["token"])
site = "https://" + cfg.jira_cloud_instance_name + ".atlassian.net/"

headers = {
  "Accept": "application/json"
}

def calculateDateDiffToToday(today, dateSTR):
    lastLogin = datetime.strptime(dateSTR, '%Y-%m-%d')
    delta = today - lastLogin
    return delta.days

r = open(dir_path + '/' + filename['results'], 'w', newline='')
r_writer = csv.writer(r)
header = ["project_key","type", "total_issues","last_issue_update_time","lead","lead_active","archival_candidate"]

def projects_check():

    print ("\nRetrieving overall info about projects... ")
    j = open(dir_path + '/' + filename['jira_projects'], 'w', newline='')

    j_writer = csv.writer(j)
    j_writer.writerow(header)
    c_total_projects = 0
    c_leadinactive = 0
    c_classic = 0
    c_nextgen = 0
    c_archival_prospect = 0
    c_project_zero_issues = 0

    today = datetime.today()

    isLast = False

    maxresult = 50
    startAt = 0
    page = 0
    while not (isLast):
        page = page + 1
        #print (page)
        url = site + "rest/api/3/project/search?expand=lead,projectKeys,insight,description&maxResults="+str(maxresult)+"&startAt="+str(startAt)
        response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
        )

        dataA = json.loads(response.text)

        #print (len(dataA["values"]))
        if (dataA["isLast"]) == True:
            isLast = True
        else:
            startAt = startAt + maxresult


        for i in dataA['values']:
            '''
            print (i['key'])
            print (i['lead']['displayName'])
            print (i['lead']['active'])
            print (i['insight']['totalIssueCount'])
            print (i['insight']['lastIssueUpdateTime'])
            #row = i['key'] + "," + str(i['insight']['totalIssueCount']) + "," + i['insight']['lastIssueUpdateTime'] + "," + i['lead']['displayName'] + "," + str(i['lead']['active'])
            '''
            row = []
            row.append(i['key'])
            row.append(i['style'])
            row.append(str(i['insight']['totalIssueCount']))
            if i['insight']['totalIssueCount'] != 0:
                row.append(i['insight']['lastIssueUpdateTime'])
            else:
                row.append("-")
            row.append(i['lead']['displayName'].encode('utf-8'))
            row.append(str(i['lead']['active']))

            c_total_projects = c_total_projects + 1

            if i['lead']['active'] == False:
                c_leadinactive = c_leadinactive + 1

            if i['style'] == "classic":
                c_classic = c_classic + 1

            elif i['style'] == "next-gen":
                c_nextgen = c_nextgen + 1

            if i['insight']['totalIssueCount'] == 0:
                c_project_zero_issues = c_project_zero_issues + 1
            else:
                timezone_unaware = i['insight']['lastIssueUpdateTime'][0:10]
                JiraDateDifferenceToToday = calculateDateDiffToToday(today, timezone_unaware)
                if JiraDateDifferenceToToday > 180:
                    c_archival_prospect = c_archival_prospect + 1
                    row.append('True')
                else:
                    row.append('False')

            j_writer.writerow(row)

    j.close()
    print("File: "+ dir_path + "/" + filename['jira_projects'] +" created")

    print ("Amount of projects: "+str(c_total_projects))
    print ("Amount of projects with inactive leads: "+str(c_leadinactive))
    print ("Amount of classic projects: "+str(c_classic))
    print ("Amount of nexgen projects: "+str(c_nextgen))
    print ("Amount of archival projects prospect due to date: "+str(c_archival_prospect))
    print ("Amount of projects with zero issues: "+str(c_project_zero_issues))

    header_variables = ["variable", "value","description"]
    r_writer.writerow(header_variables)
    row = ["c_total_projects",c_total_projects,"Amount of projects"]
    r_writer.writerow(row)
    row = ["c_leadinactive",c_leadinactive,"Amount of projects with inactive leads"]
    r_writer.writerow(row)
    row = ["c_classic",c_classic,"Amount of classic projects"]
    r_writer.writerow(row)
    row = ["c_archival_prospect",c_archival_prospect,"Amount of archival projects prospect due to date"]
    r_writer.writerow(row)
    row = ["c_project_zero_issues",c_project_zero_issues,"Amount of projects with zero issues"]
    r_writer.writerow(row)
    row = ["c_nextgen",c_nextgen,"Amount of Team-managed projects"]
    r_writer.writerow(row)

def dashboards_check():

    print ("\nRetrieving overall info about dashboards... ")
    isLast = False
    maxresult = 50
    startAt = 0
    page = 0
    total = 0
    global_count = 0

    txtf = open(dir_path + "/" + filename['dashboards_global_list'], "a")

    while not (isLast):
        page = page + 1
        #print (page)
        url = site + "rest/api/3/dashboard/search?expand=sharePermissions&maxResults="+str(maxresult)+"&startAt="+str(startAt)
        response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
        )

        dataA = json.loads(response.text)

        #print (len(dataA["values"]))
        if (dataA["isLast"]) == True:
            isLast = True
        else:
            startAt = startAt + maxresult

        for i in dataA['values']:
            total = total + 1
            #print (i)
            #print (i['sharePermissions'][0]['type'])
            #print(i['self'])
            for n in range(len(i['sharePermissions'])):
                if (i['sharePermissions'][n]['type'] == "global"):
                    #print(i['self'])
                    txtf.write(i['self']+"\n")
                    global_count = global_count + 1
            
    print ("Amount of dashboards: "+str(total))
    print ("Amount of global shared dashboards: "+str(global_count))
    row = ["c_dashboards_total",total,"Amount of dashboards"]
    r_writer.writerow(row)
    row = ["c_dashboards_global",global_count,"Amount of global shared dashboards"]
    r_writer.writerow(row)
    txtf.close()
    print("File: "+ dir_path + "/" + filename['dashboards_global_list'] + " created")


def filters_check():

    print ("\nRetrieving overall info about filters... ")
    isLast = False
    maxresult = 50
    startAt = 0
    page = 0
    total = 0
    global_count = 0

    txtf = open(dir_path + "/" + filename['filters_global_list'], "a")

    while not (isLast):
        page = page + 1
        #print (page)
        url = site + "rest/api/3/filter/search?expand=sharePermissions&maxResults="+str(maxresult)+"&startAt="+str(startAt)
        response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
        )

        dataA = json.loads(response.text)

        #print (len(dataA["values"]))
        if (dataA["isLast"]) == True:
            isLast = True
        else:
            startAt = startAt + maxresult

        for i in dataA['values']:
            total = total + 1
            #print (i)
            #print (i['sharePermissions'][0]['type'])
            #print(i['self'])
            for n in range(len(i['sharePermissions'])):
                if (i['sharePermissions'][n]['type'] == "global"):
                    #print(i['self'])
                    txtf.write(i['self']+"\n")
                    global_count = global_count + 1
            

    print ("Amount of filters: "+str(total))
    print ("Amount of global shared filters: "+str(global_count))
    row = ["c_filters_total",total,"Amount of filters"]
    r_writer.writerow(row)
    row = ["c_filters_global",global_count,"Amount of global shared filters"]
    r_writer.writerow(row)
    txtf.close()
    print("File: "+ dir_path + "/" + filename['filters_global_list'] + " created")


def issue_types_check():

    print ("\nRetrieving overall info about Issue types... ")
    isLast = False
    j = open(dir_path + "/" + filename['issue_types_usage'], 'w', newline='')
    j_writer = csv.writer(j)
    header = ["issue_type_id","issue_type_name","issue_amount"]
    j_writer.writerow(header)
    maxresult = 50
    startAt = 0
    page = 0
    total = 0
    total_issue_type_not_used = 0
    global_count = 0

    url = site +"rest/api/3/issuetype"
    response = requests.request(
    "GET",
    url,
    headers=headers,
    auth=auth
    )

    dataA = json.loads(response.text)

    for i in dataA:
        #total = total + 1
        #print (i)
        #print (i['sharePermissions'][0]['type'])
        #print(i['self'])
        #print (i)
        #break
        if "scope" not in i:
            total = total + 1
            query = {
                'jql': 'issuetype = ' + i['id']
            }
            urlsearch = site + "rest/api/3/search"
            responsesearch = requests.request(
            "GET",
            urlsearch,
            headers=headers,
            params=query,
            auth=auth
            )
            dataSearch = json.loads(responsesearch.text)
            #print (dataSearch['total'])
            if (dataSearch['total'] == 0):
                total_issue_type_not_used = total_issue_type_not_used + 1
            row = []
            row.append(i['id'])
            row.append(i['name'])
            row.append(dataSearch['total'])
            j_writer.writerow(row)
            #print (i['name'])
            #print (dataSearch['total'])
            #break

    j.close()
    print ("Total of issue types: "+str(total))
    print ("Total of issue types with 0 issues using it: "+str(total_issue_type_not_used))
    row = ["c_issue_types_total",total,"Amount of issue types"]
    r_writer.writerow(row)
    row = ["c_issue_types_unused",total_issue_type_not_used,"Amount of issue types with no issues"]
    r_writer.writerow(row)
    print("File: "+ dir_path + "/" + filename['issue_types_usage'] + " created")


def workflows_check():

    print ("\nRetrieving overall info about Workflows... ")
    today = datetime.today()
    j = open(dir_path + "/" + filename['workflows_unused'], 'w', newline='')
    j_writer = csv.writer(j)
    header = ["workflow_name","workflow_entityId", "updated","diffDateToToday"]
    j_writer.writerow(header)

    isLast = False
    url = site + "rest/api/3/workflow/search?&expand=schemes"
    response = requests.request(
    "GET",
    url,
    headers=headers,
    auth=auth
    )

    dataA = json.loads(response.text)
    TotalWorkflows = dataA["total"]

    maxresult = 50
    startAt = 0
    page = 0
    total = 0
    unused_count = 0

    while not (isLast):
        page = page + 1
        #print (page)
        url = site + "rest/api/3/workflow/search?&isActive=false&expand=schemes&maxResults="+str(maxresult)+"&startAt="+str(startAt)
        response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
        )

        dataA = json.loads(response.text)

        #print (len(dataA["values"]))
        if (dataA["isLast"]) == True:
            isLast = True
        else:
            startAt = startAt + maxresult

        for i in dataA['values']:
            total = total + 1
            #print (i)
            #print (i['sharePermissions'][0]['type'])
            #print(i['self'])
            try:
                timezone_unaware = i['updated'][0:10]
            except KeyError as ke:
                timezone_unaware = "1969-12-31"
            
            DateDifferenceToToday = calculateDateDiffToToday(today, timezone_unaware)
            if DateDifferenceToToday > 180:
                unused_count = unused_count + 1
                row = []
                row.append(i['id']['name'])
                row.append(i['id']['entityId'])
                row.append(timezone_unaware)
                row.append(DateDifferenceToToday)
                j_writer.writerow(row)

    j.close()

    TotalInactiveWorkflows = dataA["total"]

    print ("Amount of workflows: "+str(TotalWorkflows))
    print ("Amount of inactive workflows: "+str(TotalInactiveWorkflows))
    print ("Amount unused workflows: "+str(unused_count))

    row = ["c_workflows_total",TotalWorkflows,"Amount of workflows"]
    r_writer.writerow(row)
    row = ["c_workflows_unused",unused_count,"Amount of inactive workflows with over 6 months of last updated date"]
    r_writer.writerow(row)
    print("File: "+ dir_path + "/" + filename['workflows_unused'] + " created")


def screens_check():

    print ("\nRetrieving overall info about Screens... ")
    isLast = False
    maxresult = 50
    startAt = 0
    page = 0
    total = 0
    unused_count = 0

    j = open(dir_path + "/" + filename['screens_unused'], 'w', newline='')
    j_writer = csv.writer(j)
    header = ["screen_id","screen_name","screen_description"]
    j_writer.writerow(header)


    while not (isLast):
        page = page + 1
        #print (page)
        url = site + "rest/api/3/screens?expand=screenScheme%2CworkflowTransitions&maxResults="+str(maxresult)+"&startAt="+str(startAt)+"&orderBy=name&scope=GLOBAL"

        response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
        )

        dataA = json.loads(response.text)

        #print (len(dataA["values"]))
        if (dataA["isLast"]) == True:
            isLast = True
        else:
            startAt = startAt + maxresult


        for i in dataA['values']:
            total = total + 1
            #print (i)
            #print (i['sharePermissions'][0]['type'])
            #print(i['self'])
            #print(i)
            lenscreenSchemes = 0
            lenworkflowTransitions = 0

            try:
                lenscreenSchemes = len(i['screenSchemes']['values'])
            except KeyError as ke:
                lenscreenSchemes = 0
                #print('Key Not Found in Screens Dictionary:', ke)

            try:
                lenworkflowTransitions = len(i['workflowTransitions']['values'])
            except KeyError as ke:
                lenworkflowTransitions = 0
                #print('Key Not Found in Screens Dictionary:', ke)

            if lenscreenSchemes == 0 and lenworkflowTransitions == 0 :
                unused_count = unused_count + 1
                row = []
                row.append(i['id'])
                row.append(i['name'])

                try:
                    description_text = row.append(i['description'])
                except KeyError as ke:
                    description_text = ""
                    #print('Description key not found', ke)
                row.append(description_text)
                j_writer.writerow(row)

    j.close()

    print ("Amount of screens: "+str(total))
    print ("Amount of unused screens (Not used in screen schemes or workflows): "+str(unused_count))
    row = ["c_screens_total",total,"Amount of screens"]
    r_writer.writerow(row)
    row = ["c_screens_unused",unused_count,"Amount of unused screens (Not used in screen schemes or workflows)"]
    r_writer.writerow(row)
    print("File: "+ dir_path + "/" + filename['screens_unused'] + " created")

def custom_fields_check():
    
    print ("\nRetrieving overall info about Custom fields... ")
    isLast = False
    maxresult = 50
    startAt = 0
    page = 0
    total = 0
    unused_count = 0
    custom_fields_list = []
    today = datetime.today()

    j = open(dir_path + "/" + filename['custom_fields_unused'], 'w', newline='')

    j_writer = csv.writer(j)
    header = ["custom_field_id","custom_field_name", "custom_field_last_used"]
    j_writer.writerow(header)

    while not (isLast):
        page = page + 1
        #print (page)
        url = site + "rest/api/2/field/search?expand=lastUsed%2CscreensCount%2CcontextsCount%2CisLocked%2CisUnscreenable&type=custom&maxResults="+str(maxresult)+"&startAt="+str(startAt)

        response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
        )

        dataA = json.loads(response.text)
        #print(dataA)
        #print (len(dataA["values"]))
        if (dataA["isLast"]) == True:
            isLast = True
        else:
            startAt = startAt + maxresult


        for i in dataA['values']:
            total = total + 1
            custom_fields_list.append(i['name'])
            #print (i)
            #print (i['sharePermissions'][0]['type'])
            #print(i['self'])
            #print(i)


            if (i['screensCount'] == 0) and (i['isLocked'] == False):
                unused_count = unused_count + 1
                row = []
                row.append(i['id'])
                #print(i['id'])
                row.append(i['name'])
                #row.append(i['description'].encode("ASCII"))
                try:
                    timezone_unaware = i['lastUsed']["value"][0:10]
                except KeyError as ke:
                    timezone_unaware = "1969-12-31"
                    
                DateDifferenceToToday = calculateDateDiffToToday(today, timezone_unaware)
                if DateDifferenceToToday > 180:
                    row.append(timezone_unaware)
                    j_writer.writerow(row)

    j.close()

    print ("Amount of custom fields: "+str(total))
    print ("Amount of unused custom fields (Not used in screens): "+str(unused_count))

    row = ["c_custom_fields_total",total,"Amount of custom fields"]
    r_writer.writerow(row)
    row = ["c_custom_fields_unused",unused_count,"Amount of unused custom fields (Not used in screens)"]
    r_writer.writerow(row)
    print("File: "+ dir_path + "/" + filename['custom_fields_unused'] + " created")


    #checking dupes
    newlist  = []
    duplist = []

    txtf_dup = open(dir_path + "/" + filename['custom_fields_duplicates'], "a")
    txtf_uniq = open(dir_path + "/" + filename['custom_fields_unique'], "a")

    for i in custom_fields_list:
        if i not in newlist:
            newlist.append(i)
            txtf_uniq.write(i+"\n")
        else:
            duplist.append(i)
            txtf_dup.write(i+"\n")

    #print("List of duplicates", duplist)
    #print("Unique Item List", newlist)
    txtf_dup.close()
    txtf_uniq.close()
    print("File: "+ dir_path + "/" + filename['custom_fields_duplicates'] + " created")
    print("File: "+ dir_path + "/" + filename['custom_fields_unique'] + " created")
    
def statuses_check():

    print ("\nRetrieving overall info about Statuses... ")
    isLast = False
    maxresult = 50
    startAt = 0
    page = 0
    total = 0
    unused_count = 0
    statuses_list = []

    j = open(dir_path + "/" + filename['unused_statuses'], 'w', newline='')
    j_writer = csv.writer(j)
    header = ["status_id","status_name"]
    j_writer.writerow(header)


    while not (isLast):
        page = page + 1
        #print (page)
        url = site + "rest/api/3/statuses/search?expand=usages&orderBy=name&scope=GLOBAL&maxResults="+str(maxresult)+"&startAt="+str(startAt)

        response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
        )

        dataA = json.loads(response.text)

        #print (len(dataA["values"]))
        if (dataA["isLast"]) == True:
            isLast = True
        else:
            startAt = startAt + maxresult

        for i in dataA['values']:
            total = total + 1
            statuses_list.append(i['name'])
            #print (i)
            #print (i['sharePermissions'][0]['type'])
            #print(i['self'])
            #print(i)

            if (len(i['usages']) == 0):
                unused_count = unused_count + 1
                row = []
                row.append(i['id'])
                #print(i['id'])
                row.append(i['name'])
                #row.append(i['description'].encode("ASCII"))
                j_writer.writerow(row)

    j.close()

    print ("Amount of statuses: "+str(total))
    print ("Amount of unused statuses (Not used in any workflow used by a project): "+str(unused_count))

    row = ["c_statuses_total",total,"Amount of statuses"]
    r_writer.writerow(row)
    row = ["c_statuses_unused",unused_count,"Amount of unused statuses (Not used in any workflow used by a project)"]
    r_writer.writerow(row)
    print("File: "+ dir_path + "/" + filename['unused_statuses'] + " created")


    #checking dupes
    newlist  = []
    duplist = []
    #txtf_dup = open(dir_path + "/" + filename['statuses_duplicates'], "a")
    txtf_uniq = open(dir_path + "/" + filename['statuses_unique'], "a")

    for i in statuses_list:
        if i not in newlist:
            newlist.append(i)
            txtf_uniq.write(i+"\n")
        else:
            duplist.append(i)
            #txtf_dup.write(i+"\n")

    #print("List of duplicates", duplist)
    #print("Unique Item List", newlist)
    #print "\n".join(newlist)

    #txtf_dup.close()
    txtf_uniq.close()
    #print("File: "+ dir_path + "/" + filename['statuses_duplicates'] + " created")
    print("File: "+ dir_path + "/" + filename['statuses_unique'] + " created")

def updateConfluencePage():

    if cfg.confluence_page_id != "":
        print ("\nUpdating info values on Confluence page... ")
        url = "https://"+ cfg.confluence_cloud_instance_name +".atlassian.net/wiki/rest/api/content/"+ cfg.confluence_page_id +"?expand=body.storage,version"
        response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth_confluence
        )

        dataA = json.loads(response.text)

        page_storage_value = dataA["body"]["storage"]["value"]
        page_title = dataA["title"]
        page_version_number = int(dataA["version"]["number"])

        url = "https://"+ cfg.confluence_cloud_instance_name +".atlassian.net/wiki/rest/api/content/"+ cfg.confluence_page_id

        newvalue = page_storage_value

        r = open(dir_path + '/' + filename['results'])
        r_reader = r.readlines()
        n = 0
        for line in r_reader:
            if n != 0:
                x = line.split(",")
                newvalue = newvalue.replace("#"+x[0], x[1])
            n = n + 1

        r.close()

        payload = json.dumps( {
        "version": {
            "number": page_version_number+1,
            "message": "",
        },
        "title": page_title,
        "type": "page",
        "body": {
            "storage": {
            "value": newvalue,
            "representation": "storage"
            }
        }
        } )

        headers_put = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.request(
        "PUT",
        url,
        data=payload,
        headers=headers_put,
        auth=auth_confluence
        )

        print("Confluence page updated")

#Main execution stack
projects_check()
"""
dashboards_check()
filters_check()
issue_types_check()
workflows_check()
screens_check()
custom_fields_check()
statuses_check()
"""
r.close()

#updateConfluencePage()

print ("\nTotal script duration: ")
print (datetime.now() - startTime)

