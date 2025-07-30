# Serialisation Configuration

Parsing tabular data into RDF commonly involves identifying key entities, assigning them a unique identifier, linking them to their ontology-defined node-types and assigning any fundamental literals (name and description labels). In addition, where relationships exist between entities, the appropriate *Subject Predicate Object* triples need be created to define relationship structure, and the overall graph.

To achieve this, we create a serialisation.json file to map from input column names into associated objects in the final RDF representation.

All serialisation.json files are constrained by the [serialisations/serialisationschema.json](../serialisations/serialisationschema.json) json-schema file which sets out the format and legal contents of a given json config.

## Configuration File Format

The serialisation format is split into a number of named key sections:

### GlobalVariables

Here are declared any config-level global variable values in *"key" : "value"* pairs.

### NamedObjects

The NamedObjects section is partitioned into Classes. For each class to be created, the RDF class-URL is provided as the value associated to the "TargetClass" key, and for each target class, there is a list of named Instances than can be created to populate instances of that class.

Each Instance sets out values for InstanceName (an internal name to keep track of this instance), SubjectTag in which the name of the column in which the identifiers for entities of this instance are found. 

The ParentTag field allows for the construction of a *fully qualified name* which gets prepended to the SubjectTag name while building a unique name. In cases where the Parent object itself references a ParentTag in its definition, the fully qualified name will consist of the chain of object names extracted from the file separated by dots.

When using the [*mastering*](kg_mastering.md) functionality, it is the fully qualified name that is used to establish whether a given entity has been seen before, and where it has, assigned its existing URI from the master-database. If the fully qualified name is unique, then a new URI is assigned and stored in the mastering database for future use.

### Relationships

The Relationships section is partitioned by the Predicate field, which sets out the target predicate to be generated in any nested configuration. Within each Predicate section is then a list of Instances, with each instance consisting of InstanceName to name the instance internally, then SubjectTag to identify the Subject of the relationship and ObjectTag to identify the object of the relationship.

### Properties

Properties are similar to Relationships, with the exception that the object is expected to be a literal rather than another entity. Again, the section is partitioned by the Predicate field where the predicates being constructed is identified by its URL, and within this are defined a list of named Instances. In each instance, there are the fields InstanceName, containing the name for the specific instance being specified, followed by the field in which the SubjectTag can be found, followed by the field in which the literal data is located, to be populated in the LiteralTag field.
