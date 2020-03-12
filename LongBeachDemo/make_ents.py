import ruamel.yaml as yaml
import openlattice
from olpy.flight import Flight

jwt = input('Input your JWT:')

fl = Flight()
fl.deserialize("lb_demo.yaml")

configuration = openlattice.Configuration()
configuration.host = "http://localhost:8080"
configuration.api_key_prefix['Authorization'] = 'Bearer'
configuration.api_key['Authorization'] = jwt

edm_api = openlattice.EdmApi(openlattice.ApiClient(configuration))

lbfd = fl.schema

def make_ents_from_flight(fd, orgid):
    created_ents = []
    for defn in fd:
        for ent in fd[defn]:
        
            nm = fd[defn][ent]['fqn'].split('.')
            
            out = {
                "entityTypeId": edm_api.get_entity_type_id(namespace=nm[0],name=nm[1]),
                "name": fd[defn][ent]['entity_set_name'],
                "title": fd[defn][ent]['entity_set_name'],
                "contacts": ["nicholas@openlattice.com"],
                "organizationId": orgid
                
            }
            created_ents.append(out)
            
    return created_ents

entds = make_ents_from_flight(lbfd, '00000000-0000-0001-0000-000000000000')

def create_entity_sets(entlist):
    for entity in entlist:
        try:
            edm_api.create_entity_sets([entity]) 
            print(f"Created {entity['name']}\n\n")
        except openlattice.rest.ApiException as exc:
            print(exc)


create_entity_sets(entds)
