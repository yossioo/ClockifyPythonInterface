import datetime
import json
from typing import Dict, Tuple
import faster_than_requests as requests
import urllib3
from urllib.parse import urlencode

API_EP = "https://api.clockify.me/api/v1"


class ClockifyClient:
    def __init__(self, api_key, use_faster_than=False):
        print(f"Initializing ClockifyClient with API_KEY: {api_key[:4]}...")
        # self.headers = [("content-type", "application/json"), ("X-Api-Key", api_key)]
        self.headers = {"content-type": "application/json", "X-Api-Key": api_key}
        self.http = urllib3.PoolManager()
        self.use_faster_than = use_faster_than
        if self.use_faster_than:
            requests.set_headers([(k, v) for k, v in self.headers.items()])

        me = self.get_me()
        self.userId, self.userName = me["id"], me["name"]
        print(f"User: [{self.userId}] ({self.userName})")
        self.projects = {}
        self.wss = {}
        self.main_ws_id = ""
        self.update_workspaces_and_projects()
        last_project = self.get_last_project_worked_on()["name"]
        print(f"Last worked on: {last_project}")

    def utc_now(self):
        return "{0:%Y-%m-%dT%H:%M:%SZ}".format(datetime.datetime.utcnow())

    def get(self, path: str, fields: Dict = None) -> Dict:
        if not self.use_faster_than:
            r = self.http.request(
                "GET", API_EP + path, headers=self.headers, fields=fields
            )
            if r.status == 200:
                return json.loads(r.data.decode("utf-8"))
            else:
                print(f"Request <{path}> failed: {r.status}")
                return None
        else:
            result = requests.get(API_EP + path)
            if "200" in result["status"]:
                return json.loads(result["body"])
            else:
                print(f"Request <{path}> failed: {result['status']}")
                return None

    def post(self, path: str, fields: Dict = None) -> bool:
        if not self.use_faster_than:
            encoded_body = json.dumps(fields)
            r = self.http.request(
                "POST", API_EP + path, headers=self.headers, body=encoded_body
            )
            if r.status == 201:
                return True
            else:
                print(f"Request <{path}> failed: {r.status}\nr.data= {r.data}")
                for k, v in fields.items():
                    print(f" :( {k}: {v}")
                return False
        else:
            result = requests.post(API_EP + path, json.dumps(fields))
            print(result)
            raise Exception("Sorry, faster-than-request post is not supported")

    def patch(self, path: str, fields: Dict = None) -> bool:
        if not self.use_faster_than:
            encoded_body = json.dumps(fields)
            r = self.http.request(
                "PATCH", API_EP + path, headers=self.headers, body=encoded_body
            )
            if r.status == 200:
                return True
            else:
                print(f"Request <{path}> failed: {r.status}\nr.data= {r.data}")
                for k, v in fields.items():
                    print(f" :( {k}: {v}")
                return False
        else:
            result = requests.post(API_EP + path, json.dumps(fields))
            print(result)
            raise Exception("Sorry, faster-than-request post is not supported")

    def put(self, path: str, fields: Dict = None) -> bool:
        if not self.use_faster_than:
            encoded_body = json.dumps(fields)
            encoded_args = urlencode(fields)
            url = API_EP + path + "?" + encoded_args
            r = self.http.request("PUT", url, headers=self.headers, body=encoded_body)
            if r.status == 200:
                return True
            else:
                print(f"Request <{path}> failed: {r.status}\nr.data= {r.data}")
                for k, v in fields.items():
                    print(f" :( {k}: {v}")
                return False
        else:
            result = requests.put(API_EP + path, json.dumps(fields))
            print(result)
            raise Exception("Sorry, faster-than-request PUT is not supported")

    def update_workspaces_and_projects(self, set_self_main=True, report=True):
        wss = self.get_all_ws()
        for ws in wss:
            ws_id, ws_name = ws["id"], ws["name"]
            if report:
                print(f"Workspace: {ws_name}: {ws_id}")
            self.wss[ws_id] = ws
            if set_self_main:
                if self.userName in ws_name:
                    self.main_ws_id = ws_id
            for project in self.get_projects_list(ws_id):
                print(f"  ->  Project: [{project['name']}] - [{project['id']}]")
                self.projects[project["id"]] = project

    def set_main_ws(self, workspace_name: str = None, workspace_id: str = None):
        print(f"<set_main_ws> Unsupported now")

    def get_me(self):
        result = self.get("/user")
        return result

    def get_all_ws(self):
        return self.get("/workspaces")

    def get_projects_list(self, workspaceId: str):
        return self.get(f"/workspaces/{workspaceId}/projects")

    def get_project_by_name(self, project_name: str):
        for _, p in self.projects.items():
            if p["name"] == project_name:
                return p
        return None

    def get_project_ws_id(self, project_name: str = None, project: Dict = None):
        if project_name:
            if project:
                raise Exception(
                    "get_project_ws_id: Sorry, you cannot specify both project and project name"
                )
            project = self.get_project_by_name(project_name)
            if not project:
                return None
        return project["workspaceId"]

    def get_time_entries(
        self, workspaceId: str = None, amount: int = 10, in_progress: bool = None
    ):
        if not workspaceId:
            workspaceId = self.main_ws_id
        fields = {"page-size": amount}
        if in_progress is not None:
            fields["in-progress"] = in_progress
        return self.get(
            f"/workspaces/{workspaceId}/user/{self.userId}/time-entries", fields=fields
        )

    def get_active_entry(self, workspaceId: str = None):
        return self.get_time_entries(workspaceId, 1, in_progress=True)[0]

    def get_last_project_worked_on(self, workspaceId: str = None):
        te = self.get_time_entries(workspaceId, 1, in_progress=False)[0]
        return self.te_project_name(te)

    def start_new_time_entry_in_project(self, project_name: str, description: str = ""):
        project = self.get_project_by_name(project_name)
        w_id = self.get_project_ws_id(project=project)
        return self.start_new_time_entry(w_id, project["id"], description)

    def start_new_time_entry(
        self, workspaceId: str, projectId: str, description: str = ""
    ):
        fields = {
            "description": description,
            "projectId": projectId,
            "start": self.utc_now(),
        }
        return self.post(f"/workspaces/{workspaceId}/time-entries", fields=fields)

    def stop_current_time_entry(self):
        te = self.get_active_entry()
        return self.patch(
            f"/workspaces/{te['workspaceId']}/user/{self.userId}/time-entries",
            fields={"end": self.utc_now()},
        )

    def update_new_task(self):
        pass

    def start_working(self, project: str, workspaceId: str = None):
        pass

    def te_project_name(self, time_entry_inst: Dict):
        return self.projects[time_entry_inst["projectId"]]
