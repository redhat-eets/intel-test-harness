import pytest
  
from kubernetes import client, config
from openshift.dynamic import DynamicClient

@pytest.fixture(scope="module")
def oc_client():
    k8s_client = config.new_client_from_config()
    return DynamicClient(k8s_client)

