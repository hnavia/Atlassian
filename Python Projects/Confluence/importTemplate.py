import requests
from requests.auth import HTTPBasicAuth
import json

# INSERT "USER", "TOKEN", "BASE_URL" HERE
USER = ""
TOKEN = ""
BASE_URL = ""

url = BASE_URL + "/wiki/rest/api/template"

auth = HTTPBasicAuth(USER, TOKEN)

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "templateId": "1409024118",
  "name": "Release notes template - server",
  "description": "Use this template for server release notes.",
  "labels": [],
  "templateType": "page",
  "editorVersion": "v2",
  "body": {
    "storage": {
      "value": "<ac:layout><ac:layout-section ac:type=\"fixed-width\" ac:breakout-mode=\"default\"><ac:layout-cell><p style=\"text-align: center;\"><strong>Release date</strong>:&nbsp;<ac:placeholder>Feb 23rd, 2020</ac:placeholder></p><p style=\"text-align: center;\">Our team is excited to announce the release of <ac:placeholder>&lt;the app&gt;</ac:placeholder>, version <ac:placeholder>&lt;number&gt;</ac:placeholder>.</p><p style=\"text-align: center;\"><ac:placeholder>&lt;Video for major releases or GIF for minor or none for bug fixes&gt;</ac:placeholder></p><hr /></ac:layout-cell></ac:layout-section><ac:layout-section ac:type=\"two_equal\" ac:breakout-mode=\"wide\"><ac:layout-cell><p><strong>Highlights</strong></p><ul><li><p><a href=\"https://bobswift.atlassian.net/wiki/spaces/TBL/pages/1137738312/Sample+Release+Notes+Template+3#Topic-1\">Topic 1</a></p></li><li><p><a href=\"https://bobswift.atlassian.net/wiki/spaces/TBL/pages/1137738312/Sample+Release+Notes+Template+3#Topic-2\">Topic 2</a></p></li><li><p><a href=\"https://bobswift.atlassian.net/wiki/spaces/TBL/pages/1137738312/Sample+Release+Notes+Template+3#Resolved-issues\">Resolved issues</a></p></li></ul><hr /><p><strong>Downloads</strong></p><p><a href=\"https://marketplace.atlassian.com/\">Visit Marketplace</a></p></ac:layout-cell><ac:layout-cell><p><strong>Compatibility</strong><br />Compatible Jira/Confluence versions: <ac:placeholder>Version number &lt;7.0&gt;</ac:placeholder>and above</p><hr /><p><strong>Quick tip</strong><br />Did you know <ac:placeholder>&lt;this&gt;</ac:placeholder> feature can be conditioned in a jiffy? Refer to <ac:placeholder>&lt;link to example/KB article/feature&gt;</ac:placeholder></p><hr /><p><strong>Questions and feedback</strong></p><ul><li><p><ac:placeholder>Stuck with something? Raise a ticket with our&nbsp;</ac:placeholder><a href=\"https://bobswift.atlassian.net/\">support team</a>.</p></li><li><p><ac:placeholder>Do you love using our app? Let us know what you think&nbsp;</ac:placeholder><a href=\"https://marketplace.atlassian.com/apps/197/advanced-tables-for-confluence?hosting=cloud&amp;tab=reviews\">here</a>.<br /></p></li></ul></ac:layout-cell></ac:layout-section><ac:layout-section ac:type=\"fixed-width\" ac:breakout-mode=\"default\"><ac:layout-cell><hr /><h1>Topic 1</h1><p><ac:placeholder>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</ac:placeholder></p><h1>Topic 2</h1><p><ac:placeholder>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</ac:placeholder></p><hr /><h1>Resolved issues</h1><p><ac:placeholder>&lt;List of resolved issues&gt;</ac:placeholder></p><hr /><h3><strong>Credits</strong></h3><p>Thank you our valuable customers!</p><p>We want to thank you, our incredible, supportive customers, for using our apps.&nbsp;You have provided great feedback and want you to know that&nbsp;<u>you</u>&nbsp;truly are the reason why we build software!</p><ac:structured-macro ac:name=\"details\" ac:schema-version=\"1\" data-layout=\"default\" ac:macro-id=\"10497f81-093d-4ace-8b0b-39d1430b23aa\"><ac:parameter ac:name=\"hidden\">true</ac:parameter><ac:parameter ac:name=\"id\">ReleaseNotes</ac:parameter><ac:rich-text-body><table data-layout=\"default\"><tbody><tr><th data-highlight-colour=\"#ffffff\"><p><strong>Release Date</strong></p></th><th data-highlight-colour=\"#ffffff\"><p><ac:placeholder>Release date</ac:placeholder></p></th></tr><tr><th><p><strong>Version</strong></p></th><td><p><ac:placeholder>Version number </ac:placeholder></p></td></tr><tr><th><p><strong>Purpose</strong></p></th><td><p><ac:placeholder>List of highlights</ac:placeholder></p></td></tr></tbody></table></ac:rich-text-body></ac:structured-macro></ac:layout-cell></ac:layout-section></ac:layout>",
      "representation": "storage",
      "embeddedContent": []
    }
  },
  "_links": {
    "self": "https://bobswift.atlassian.net/wiki/rest/api/template/1409024118",
    "base": "https://bobswift.atlassian.net/wiki",
    "context": "/wiki"
  }
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))