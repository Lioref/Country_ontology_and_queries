import rdflib


def prime_minister_count_query(ontology):
    q = """
    select (COUNT(distinct ?person) as ?sum)
    WHERE
    {
        ?person <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Person> .
        ?person <https://en.wikipedia.org/wiki/Job> <https://en.wikipedia.org/wiki/Prime_minister> .
    }
    """
    res = ontology.query(q)
    return list(res)


def country_count_query(ontology):
    q = """
        SELECT(COUNT(distinct ?country) as ?sum)
        WHERE
        {
        ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country>.
        }
        """
    res = ontology.query(q)
    return list(res)


def republic_count_query(ontology):
    q = """
        select (COUNT(distinct ?country) as ?num_republics)
        WHERE
        {
            ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
            ?country <https://en.wikipedia.org/wiki/Government> ?gov .
            FILTER ( contains(str(?gov), "Republic") || contains(str(?gov), "republic"))
        }
        """
    res = ontology.query(q)
    return list(res)


def monarchy_count_query(ontology):
    q = """
    select (COUNT(distinct ?country) as ?sum)
    WHERE
    {
        ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
        ?country <https://en.wikipedia.org/wiki/Government> ?gov .
        FILTER(contains(str(?gov), "monarchy") || contains(str(?gov), "Monarchy"))
    }
    """
    res = ontology.query(q)
    return list(res)


def main():
    # load ontology
    country_graph = rdflib.Graph()
    country_graph.parse("country_ontology.nt", format="nt")

    # prime minister count
    pm_count = prime_minister_count_query(country_graph)
    print("prime minister count query:")
    for r in pm_count:
        print(r)

    # country count
    country_count = country_count_query(country_graph)
    print("country count query:")
    for r in country_count:
        print(r)

    # republic count 
    republic_count = republic_count_query(country_graph)
    print("republic count query:")
    for r in republic_count:
        print(r)

    # monarchy count
    monarchy_count = monarchy_count_query(country_graph)
    print("monarchy count query:")
    for r in monarchy_count:
        print(r)

    return 

if __name__ == '__main__':
    main()
    print('Done.')