# Mastering Entities in a Knowledge Graph

Knowledge graphs make integrating disparate datasets easy, but this ease rests heavily on the important assumption that entities can be identified uniquely and unambiguously across the source-data estate.

>[!NOTE]
>Aliases to the same individual can be addressed with owl:sameAs linkages (classes and properties that share equivalence should use owl:equivalentClass and owl:equivalentProperty, and for entities of type skos:Concept, there's the option of using skos:exactMatch and skos:closeMatch to denote equivalence).

Assigning owl:sameAs links provides a patch to connect entities that are equivalent but which have been assigned different URIs, but at a cost in terms of complexity and volume.

Ideally, we should have a method for unambiguously naming everything in our domain such that everything can be uniquely addressed.

*kgontologies* provides a framework for establishing unique names for things, and methods for serialising and constructing triples that make use of those names consistently in a process called Mastering.

