# Libraries
import requests
import json
from wisski.api import Api, Pathbuilder, Entity
from pymongo import MongoClient
from SPARQLWrapper import JSON, SPARQLWrapper

"""
This self-contained module is for performing CRUD Insert/Update function for projects data
on the WissKI system in hosted on 132.180.10.89
"""


class Core:

    @staticmethod
    def set_api_auth(pathbuilder_name: str | None = None) -> Api:
        with open('dicts/config.json', 'r') as file:
            _auth_dict = json.load(file).get('wisski')
            file.close()
        _api = Api(
            base_url=_auth_dict.get('wisski_endpoint'),
            auth=(_auth_dict.get('username'), _auth_dict.get('password')),
            headers={"Cache-Control": "no-cache"}
        )
        if pathbuilder_name:
            _api.pathbuilders = [pathbuilder_name]
        else:
            _api.pathbuilders = [_auth_dict.get('pathbuilder')]
        return _api

    @staticmethod
    def entity_uri(search_value: str, qualifier: str | None = None, query_string: str):
        with open('dicts/config.json', 'r') as file:
            _auth_dict = json.load(file).get('sparql')
            file.close()
        sparql = SPARQLWrapper(_auth_dict.get('endpoint'))
        sparql.setReturnFormat(JSON)
        sparql.setHTTPAuth('BASIC')
        sparql.setCredentials(_auth_dict.get('username'),
                              _auth_dict.get('password'))
        if qualifier:
            sparql.setQuery(query_string.format({
                "term": search_value,
                "authority": qualifier
            }))
        else:
            sparql.setQuery(query_string.format(search_value=search_value))


    @staticmethod
    def mongo_data(project_ids: list[str] | str):
        with open('dicts/config.json', 'r') as file:
            _auth = json.load(file).get('mongo_uri')
            file.close()
        mongo_client = MongoClient(_auth)
        project_db = mongo_client['dev']
        project_collection = project_db['projectInfo']
        if isinstance(project_ids, list):
            return list(project_collection.find({"Project_ID" : {"$in": project_ids}}))
        else:
            return list(project_collection.find({"Project_ID": project_ids}))


class ProjectFields:

    def __init__(self, document: dict | None = None):
        self._source_url: str = "https://raw.githubusercontent.com/AM-Digital-Research-Environment/rdi_wisski_importer/refs/heads/main"
        self._dicts = {
            'fields': requests.get(f'{self._source_url}/dicts/fields.json').json(),
            'bundles': requests.get(f'{self._source_url}/dicts/bundles.json').json(),
            'queries': requests.get(f'{self._source_url}/dicts/sparql_queries.json').json()
        }
        self._project_document = document
        if document:
            self._project_fields = {
                self._dicts.get('fields').get('f_project_id'): self.identifier,
                self._dicts.get('fields').get('f_project_name'): self.name,
            }

    @property
    def identifier(self):
        if self._project_document.get('Project_ID'):
            return self._project_document.get('Project_ID')
        else:
            return None

    @property
    def name(self):
        if self._project_document.get('Project_Name'):
            return self._project_document.get('Project_Name')
        else:
            return None

    @property
    def duration(self):
        if self._project_document.get('f_proj_duration'):
            return self._project_document.get('f_proj_duration')
        else:
            return None

    @property
    def institution(self):
        if self._project_document.get('f_proj_assoc_institution'):
            return self._project_document.get('f_proj_assoc_institution')
        else:
            return None

    @property
    def research_section(self):
        if self._project_document.get('f_proj_research_section'):
            _research_sections = self._project_document.get('f_proj_assoc_institution')
            for topic in
        else:
            return None


class ProjectManage(ProjectFields):

    _document = {}

    def set_document(self, document: dict):
        setattr(self, "_document", document)
        super().__init__(self._document)

    def set_mode(self, run_mode: int):
        mode_dict = {
            0: 'insert',
            1: 'update'
        }
        if mode_dict.get(run_mode) not in ['insert', 'update']:
            print('Please insert 0 for insert and 1 for update.')
        else:
            setattr(self, '_function', mode_dict.get(run_mode))

    def insert(self):
        pass

    def update(self):
        pass

    def run(self):

        match self._function:

            case "insert":
                pass

            case "update":
                pass

            case _:
                raise Exception("No run mode specified. Use set_mode method to set run mode (0/1).")
