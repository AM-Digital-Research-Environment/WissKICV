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
    def set_api(pathbuilder_name: str | None = None) -> Api:
        with open('dicts/config.json', 'r') as file:
            _auth_dict = json.load(file).get('wisski')
            file.close()
        _api = Api(
            base_url=_auth_dict.get('endpoint'),
            auth=(_auth_dict.get('username'), _auth_dict.get('password')),
            headers={"Cache-Control": "no-cache"}
        )
        if pathbuilder_name:
            _api.pathbuilders = [pathbuilder_name]
        else:
            _api.pathbuilders = [_auth_dict.get('pathbuilder')]
        return _api

    @staticmethod
    def entity_uri(search_value: str, qualifier: str | None = None, query: str | None = None):
        with open('dicts/config.json', 'r') as file:
            _auth_dict = json.load(file).get('sparql')
            file.close()
        sparql = SPARQLWrapper(_auth_dict.get('endpoint'))
        sparql.setReturnFormat(JSON)
        sparql.setHTTPAuth('BASIC')
        sparql.setCredentials(_auth_dict.get('username'),
                              _auth_dict.get('password'))
        if query:
            if qualifier:
                sparql.setQuery(query.format({
                    "term": search_value,
                    "authority": qualifier
                }))
            else:
                sparql.setQuery(query.format(search_value=search_value))


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
                self._dicts.get('fields').get('f_proj_duration'): self.duration,
                self._dicts.get('fields').get('f_proj_assoc_institution'): self.institution,
                self._dicts.get('fields').get('f_proj_research_section'): self.research_section
            }

    @property
    def identifier(self) -> list:
        if self._project_document.get('id'):
            return [self._project_document.get('Project_ID')]
        else:
            return []

    @property
    def name(self) -> list:
        if self._project_document.get('name'):
            return [self._project_document.get('Project_Name')]
        else:
            return []

    @property
    def duration(self) -> list:
        if self._project_document.get('duration'):
            return [self._project_document.get('f_proj_duration')]
        else:
            return []

    @property
    def institution(self) -> list:
        if self._project_document.get('institutions'):
            return [self._project_document.get('f_proj_assoc_institution')]
        else:
            return []

    @property
    def research_section(self):
        if self._project_document.get('researchSection'):
            _research_sections = self._project_document.get('f_proj_assoc_institution')
            _res_section_list = []
            for topic in _research_sections:
                _res_section_list.append(Core.entity_uri(search_value=topic,
                                                         qualifier="66fbf3043e468",
                                                         query_string=self._dicts.get('queries').get('genre')))
            return _res_section_list
        else:
            return []

    # Todo: Generate Enity object for associated persons
    @property
    def associated_persons(self) -> list:
        return []

class ProjectManage(ProjectFields):

    _api = Core.set_api()
    _document = {}
    _function = ""
    _edit_entity = Entity()


    def set_document(self, document: dict):
        setattr(self, "_document", document)
        super().__init__(self._document)

    def set_mode(self, run_mode: int):
        mode_dict = {
            0: 'insert',
            1: 'update'
        }
        if mode_dict.get(run_mode) not in ['insert', 'update']:
            print('Please set run_mode value 0 for insert and 1 for update.')
        else:
            setattr(self, '_function', mode_dict.get(run_mode))

    @property
    def generate_entity(self) -> Entity:
        """
        :argument: bson document/dict object to be inserted to wisski
        :return: if dry_run set to true return staged data else save entity
        """
        _project_entity_obj = Entity(self._api,
                                     bundle_id=self._dicts.get('bundle').get('g_project'),
                                     fields=self._project_fields)
        return _project_entity_obj

    def update(self, dre_id: str | list[str], fields: str | list[str]) -> Entity:

        _fields = [fields] if isinstance(fields, str) else fields
        _ids = [dre_id] if isinstance(dre_id, str) else dre_id

        for doc_id in _ids:
            setattr(self,
                    "_edit_entity",
                    Core.entity_uri(search_value=doc_id,
                                    query=self._dicts.get('dreID')))
            # Todo: Verification Stage
#            for _field in self._edit_entity.fields.keys():
#                if all(isinstance(elem, Entity) for elem in self._edit_entity.fields[_field]):
#                    for ent in self._edit_entity.fields[_field]:


    def run(self, dry_run: bool = False):

        match self._function:

            case "insert":
                if dry_run:
                    return self.generate_entity.fields
                else:
                    self._api.save(self.generate_entity)

            case "update":
                pass

            case _:
                raise Exception("No run mode specified. Use set_mode method to set run mode (0/1).")
