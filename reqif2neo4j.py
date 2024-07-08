from neo4j import GraphDatabase
import TReqzmaster

#Fragen: 
# Soll ich hier Methoden draus machen ?
# Bei Spezifikationen/Dokumenten fehlen Attribute 
# Header fehlt
# Namen für Beziehungen hinterlegen, um sie ggf Kategorisieren zu können?

# Neo4j Connection
uri = "neo4j://localhost:7687" 
auth = ("neo4j", "Benni1998") 

#Path to ReqIF File
reqifFile = r"C:\Users\Benja\Downloads\chapter2.reqif"
#Create a reqif object
reqif = TReqzmaster.TReqz.reqif(reqifFile)
document_ids = reqif.getAllDocumentIds()
documents = reqif.getAllDocuments()
links = reqif.getObjects(reqif.getLinkIds())

with GraphDatabase.driver(uri, auth=auth) as driver:    
    driver.verify_connectivity()    
    
    with driver.session() as session:
        #Deletes all Nodes and Relationships
        session.run("MATCH (n) DETACH DELETE n")
        #Creates Root Node
        session.run("CREATE (:Root {name: 'ReqIF-Root'})")
        
        #Creates Document Nodes without their Values
        for document in documents:
            document_id = document.identifier
            document_long_name = document.long_name
            session.run("""
            MATCH (root:Root {name: 'ReqIF-Root'})
            CREATE (spec:Spezification {ID: $ID, LongName: $LongName})
            MERGE (root)-[:CONTAINS]->(spec)
            """, ID=document_id, LongName=document_long_name)
        
        #Create Requirement Nodes with their Values
        for document_id in document_ids:
            allRequirements = reqif.getAllDocumentRequirementIds(document_id)
            for requirement in allRequirements:
                values = reqif.getRequirementValues(requirement, convertEnums = True)
                session.run("""
                        MERGE (document:Document {ID: $document_id})
                        CREATE (requirement:Requirement {ID: $requirement_id})
                        SET requirement += $values
                        MERGE (document)-[:CONTAINS]->(requirement)
                        """, document_id=document_id, requirement_id=requirement, values=values)

        #Create Hierachy between Requirements
            child_parent_map = reqif.getChildParentMapForDocument(document_id)
            for child, parent in child_parent_map.items():
                session.run("""
                            MATCH (child:Requirement {ID: $child})
                            MATCH (parent:Requirement {ID: $parent})
                            MERGE (parent)-[:IS_PARENT_OF]->(child)
                            """, child=child, parent=parent)
            
        #Create Links between Requirements
        for link in links:
            sourceId = None if link.source == None else link.source.identifier
            targetId = None if link.target == None else link.target.identifier
            session.run("""
                        MATCH (source:Requirement {ID: $source})
                        MATCH (target:Requirement {ID: $target})
                        MERGE (source)-[:LINK_TO]->(target)
                        """, source=sourceId, target=targetId)


        




