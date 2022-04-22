import requests
import time

from openshift.dynamic.exceptions import ApiException
from openshift.dynamic.exceptions import NotFoundError

def get_oc_projects(oc_client):

    v1_projects = oc_client.resources.get(api_version='project.openshift.io/v1',
                                          kind='Project')

    project_list = v1_projects.get()

    projects = []
    for project in project_list.items:
        projects.append(project.metadata.name)
    return projects

def test_ns(oc_client):
    assert "default" in get_oc_projects(oc_client), "didn't find default namespace"
