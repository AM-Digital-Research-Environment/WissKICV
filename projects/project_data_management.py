# Libraries
import requests
import json
from wisski.api import Api, Pathbuilder, Entity

"""
This self-contained module is for performing CRUD Insert/Update function for projects data
on the WissKI system in hosted on 132.180.10.89
"""




class ProjectManage:

    def __init__(self, function: str = "update"):
        if function in ['insert', 'update']:
            self._function = function
        self._dicts = self._dictionaries
        self._api = self._set_auth

    def _dictionaries(self,
                      source_url: str = "https://raw.githubusercontent.com/AM-Digital-Research-Environment/rdi_wisski_importer/refs/heads/main"):
        self._dicts = {
            "fields": requests.get(f'{source_url}/dicts/fields.json').json(),
            "bundles": requests.get(f'{source_url}/dicts/bundles.json').json()
        }

    @staticmethod
    def _set_auth(self) -> Api:
        with open('dicts/config.json', 'r') as file:
            data = json.load(file)
            file.close()
        _api = Api(
            base_url=data.get('base_url'),
            auth=(data.get('username'), data.get('password')),
            headers={"Cache-Control": "no-cache"}
        )
        _api.pathbuilders = [data.get('wisski_pathbuilder')]
        return _api
    