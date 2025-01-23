# Libraries
import requests
import pandas as pd
import json
from datetime import datetime
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
                sparql.setQuery(query.format(term=search_value, authority=qualifier))
            else:
                sparql.setQuery(query.format(search_value=search_value))

        query_response = sparql.queryAndConvert()
        return str(query_response["results"]["bindings"][0]["id"]["value"])

    @staticmethod
    def mongo_data(project_ids: list[str] | str):
        with open('dicts/config.json', 'r') as file:
            _auth = json.load(file).get('mongo_uri')
            file.close()
        mongo_client = MongoClient(_auth)
        project_db = mongo_client['dev']
        project_collection = project_db['projectsData']
        if isinstance(project_ids, list):
            return list(project_collection.find({"id": {"$in": project_ids}}))
        else:
            return list(project_collection.find({"id": project_ids}))


class ProjectFields:

    def __init__(self, document: dict | None = None):
        self._source_url: str = "https://raw.githubusercontent.com/AM-Digital-Research-Environment/rdi_wisski_importer/refs/heads/main"
        self._dicts = {
            'fields': requests.get(f'{self._source_url}/dicts/fields.json').json(),
            'bundles': requests.get(f'{self._source_url}/dicts/bundles.json').json(),
            'queries': requests.get(f'{self._source_url}/dicts/sparql_queries.json').json()
        }
        self._project_document = document

    def _project_fields(self):
        return {
            self._dicts.get('fields').get('f_project_id'): self.identifier,
            self._dicts.get('fields').get('f_project_name'): self.name,
            self._dicts.get('fields').get('f_proj_duration'): self.duration,
            self._dicts.get('fields').get('f_proj_assoc_institution'): self.institution,
            self._dicts.get('fields').get('f_proj_research_section'): self.research_section,
            self._dicts.get('bundles').get('g_project_assoc_person'): self.associated_persons,
            self._dicts.get('fields').get('f_proj_summary'): self.summary,
        }

    @property
    def identifier(self) -> list:
        if self._project_document.get('id'):
            return [self._project_document.get('id')]
        else:
            return []

    @property
    def name(self) -> list:
        if self._project_document.get('name'):
            return [self._project_document.get('name')]
        else:
            return []

    @property
    def duration(self) -> list:
        if self._project_document.get('date'):
            date = self._project_document.get('date')
            start = "⃰2018" if pd.isna(date.get('start')) else date.get('start').strftime("%Y")
            end = "⃰2025" if pd.isna(date.get('end')) else date.get('end').strftime("%Y")
            return [start + " - " + end]
        else:
            return []

    @property
    def institution(self) -> list:
        if self._project_document.get('institutions'):
            _inst_list = []
            for inst in self._project_document.get('institutions'):
                _inst_list.append(
                    Core.entity_uri(
                        search_value=inst,
                        query=self._dicts.get('queries').get('institution')
                    )
                )
            return _inst_list
        else:
            return []

    @property
    def research_section(self):
        if self._project_document.get('researchSection'):
            _research_sections = self._project_document.get('researchSection')
            _res_section_list = []
            for topic in _research_sections:
                _res_section_list.append(Core.entity_uri(search_value=topic,
                                                         qualifier="66fbf3043e468",
                                                         query=self._dicts.get('queries').get('genre')))
            return _res_section_list
        else:
            return []

    @property
    def associated_persons(self) -> list:
        _associated_persons_list = []
        for role, role_mapped in {'pi': 'Research team head', 'members': 'Research team member'}.items():
            if not isinstance(self._project_document.get(role), float):
                for person in self._project_document.get(role):
                    _associated_persons_list.append(
                        Entity(
                            api=Core.set_api(),
                            fields={
                                self._dicts.get('fields').get('f_proj_assoc_pers_role'): [Core.entity_uri(
                                    search_value=role_mapped,
                                    query=self._dicts.get('queries').get('role')
                                )],
                                self._dicts.get('fields').get('f_proj_assoc_pers_role_holder'): [Core.entity_uri(
                                    search_value=person,
                                    query=self._dicts.get('queries').get('person')
                                )]
                            },
                            bundle_id=self._dicts.get('bundles').get("g_project_assoc_person")
                        )
                    )
        return _associated_persons_list

    @property
    def summary(self):
        if not pd.isna(self._project_document.get('description')):
            return [self._project_document.get('description')]
        else:
            return []


class ProjectManage(ProjectFields):

    _api = Core.set_api()

    def __init__(self):
        super().__init__()
        self._function = ""
        self._edit_entity = ""

    def set_document(self, document: dict):
        setattr(self, "_project_document", document)

    def set_mode(self, run_mode: int):
        mode_dict = {
            0: 'insert',
            1: 'update'
        }
        if mode_dict.get(run_mode) not in ['insert', 'update']:
            print('Please set run_mode value 0 for insert and 1 for update.')
        else:
            setattr(self, '_function', mode_dict.get(run_mode))

    def generate_entity(self) -> Entity:
        """
        :argument: bson document/dict object to be inserted to wisski
        :return: if dry_run set to true return staged data else save entity
        """
        _project_entity_obj = Entity(self._api,
                                     bundle_id=self._dicts.get('bundles').get('g_project'),
                                     fields=self._project_fields())
        return _project_entity_obj

    def update_fields(self) -> dict:
        def get_key(value):
            try:
                return list(self._dicts.get('fields').keys())[list(self._dicts.get('fields').values()).index(value)]
            except ValueError:
                return list(self._dicts.get('bundles').keys())[list(self._dicts.get('bundles').values()).index(value)]
        setattr(self,
                "_edit_entity",
                self._api.get_entity(Core.entity_uri(search_value=self._project_document.get('id'),
                                                     query=self._dicts.get('queries').get('projectid'))))
        _fields_for_update = []
        _fields_keys = []
        compare_list = self._project_fields()
        for _field in self._edit_entity.fields.keys():
            if self._edit_entity.fields[_field] != compare_list.get(_field):
                _fields_for_update.append(_field)
                _fields_keys.append(get_key(_field))

        return {'ids': list(set(_fields_for_update)), 'keys':  list(set(_fields_keys))}

    def run(self, dry_run: bool = False):

        match self._function:

            case "insert":
                if dry_run:
                    return self.generate_entity().fields
                else:

                    self._api.save(self.generate_entity())

            case "update":
                if dry_run:
                    print("Fields to be updated are:\n" + "\n".join(self.update_fields()['keys']))
                else:
                    _source_data = self._project_fields()
                    for _field_ids in self.update_fields()['ids']:
                        self._edit_entity.fields[_field_ids] = _source_data[_field_ids]
                    self._api.save(self._edit_entity)
            case _:
                raise Exception("No run mode specified. Use set_mode method to set run mode (0/1).")
