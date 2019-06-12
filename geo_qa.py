import rdflib
import re
import os
import argparse
from lxml import html
import lxml
import pickle
import requests
from rdflib import URIRef, Literal, XSD
import unicodedata


# basic urls
COUNTRY_WIKI_URL = "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population"
WIKIPEDIA_BASE_URL = "https://en.wikipedia.org"

# ---------------------------------------------#
# -----------TEMPLATES FOR QUERIES-------------#
# ---------------------------------------------#
query_formats = {}

# president query
query_formats['presi'] = """SELECT ?person
                            WHERE
                            {
                                ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
                                FILTER (contains(lcase(str(?country)), "%s"))
                                ?person <https://en.wikipedia.org/wiki/President> ?country .
                            }
                         """
# prime minister query
query_formats['prime'] = """SELECT ?person
                            WHERE
                            {
                                ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
                                FILTER (contains(lcase(str(?country)), "%s"))
                                ?person <https://en.wikipedia.org/wiki/Prime_minister> ?country .
                            }
                         """
# population query
query_formats['popul'] = """SELECT ?population
                            WHERE
                            {
                                ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
                                FILTER (contains(lcase(str(?country)), "%s"))
                                ?country <https://en.wikipedia.org/wiki/Population> ?population .
                            }
                            """
# area query
query_formats['area'] = """SELECT ?area
                           WHERE
                           {
                                ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
                                FILTER (contains(lcase(str(?country)), "%s"))
                                ?country <https://en.wikipedia.org/wiki/Area> ?area .
                           }
                           """
# capital query
query_formats['capital'] = """SELECT ?capital
                              WHERE
                              {
                                ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
                                FILTER (contains(lcase(str(?country)), "%s"))
                                ?capital <https://en.wikipedia.org/wiki/Capital_city> ?country .
                              }
                              """
# president birthday query
query_formats['presi_bday'] = """SELECT ?bday
                                 WHERE
                                 {
                                    ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
                                    FILTER (contains(lcase(str(?country)), "%s"))
                                    ?person <https://en.wikipedia.org/wiki/President> ?country .
                                    ?person <https://en.wikipedia.org/wiki/Birthday> ?bday .
                                 }
                              """
# prime minister birthday query
query_formats['prime_bday'] = """SELECT ?bday
                                 WHERE
                                 {
                                    ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
                                    FILTER (contains(lcase(str(?country)), "%s"))
                                    ?person <https://en.wikipedia.org/wiki/Prime_minister> ?country .
                                    ?person <https://en.wikipedia.org/wiki/Birthday> ?bday .
                                 }
                              """
# who is person query
query_formats['who'] = """SELECT ?position ?country
                          WHERE
                          {
                           ?cand <https://en.wikipedia.org/wiki/Job> ?position .
                           FILTER (contains(lcase(str(?cand)), "%s"))
                           ?cand ?position ?country
                           }
                        """
# what is the government type of country
query_formats['gov'] = """SELECT ?gov_type
                          WHERE
                          {
                            ?country <https://en.wikipedia.org/wiki/Is-a> <https://en.wikipedia.org/wiki/Country> .
                            FILTER (contains(lcase(str(?country)), "%s"))
                            ?country <https://en.wikipedia.org/wiki/Government> ?gov_type .
                          }
                       """

# regular expressions for matching questions
presi_re = "^Who(\s+)is(\s+)the(\s+)president(\s+)of(\s+\w+)+(\s*)(\?+)(\s*)$"
prime_re = "^Who(\s+)is(\s+)the(\s+)prime(\s+)minister(\s+)of(\s+\w+)+(\s*)(\?+)(\s*)$"
population_re = "^What(\s+)is(\s+)the(\s+)population(\s+)of(\s+\w+)+(\s*)(\?+)$"
area_re = "^What(\s+)is(\s+)the(\s+)area(\s+)of(\s+\w+)+(\s*)(\?+)(\s*)$"
govern_re = "^What(\s+)is(\s+)the(\s+)government(\s+)of(\s+\w+)+(\s*)(\?+)(\s*)$"
capital_re = "^What(\s+)is(\s+)the(\s+)capital(\s+)of(\s+\w+)+(\s*)(\?+)(\s*)$"
presi_bday_re = "^When(\s+)was(\s+)the(\s+)president(\s+)of((\s\w+)+)(\s)born(\s*)(\?+)(\s*)$"
prime_bday_re = "^When(\s+)was(\s+)the(\s+)prime(\s+)minister(\s+)of((\s\w+)+)(\s)born(\s*)(\?+)(\s*)$"
who_re = "^Who(\s+)is(\s+)(\w+)(\s*)(\w*)(\s*)(\?+)(\s*)"


# ---------------------------------------------#
# ------FUNCTIONS FOR BUILDING ONTOLOGY--------#
# ---------------------------------------------#

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')


def clean_number(num_string):
    """
    remove none numeric chars from string repersenting
    a number. if string doesn't repersent a number at
    all, this will throw an exception.
    :param num_string: string repersenting a number
    :return: integer of the repersented number
    """
    clean_num = ''.join([c for c in num_string if str.isnumeric(c)])
    if len(clean_num) > 0:
        return int(clean_num)
    else:
        return None


def get_country_links(countries_wiki_url):
    """
    given a url to the wikipedia page listing all
    countries in the world, return a dictionary mapping
    country names to links to their respective wikipedia
    pages.
    :param countries_wiki_url: link
    :return: name (str) -> link dict (str)
    """
    # get page and parse it
    country_res = requests.get(countries_wiki_url)
    country_page = html.fromstring(country_res.content)

    # get links for countries that are not territories of another country
    non_teritories = country_page.xpath("//table[1]//td[descendant::span[@class='flagicon'] or descendant::a[@title and @href]]/a[@title and @href]")
    teritories = country_page.xpath("//table[1]//td/i[a[@href and @title]][1]/a[not(@class)][1]")

    # union for iteration
    country_link_elements = non_teritories + teritories

    country_links = {}  # maps country names to links
    for link in country_link_elements:
        if 'title' in link.attrib:
            normed_name = normalize_text(link.text)
            country_links[normed_name] = link.attrib['href']

    return country_links


def get_pres_prime_bday(president_link):
    """
    get the birthday string of the president
    birth day from wikipedia page
    :param president_link: link to president wikipedia page
    :return: string repersenting birth date
    """
    res = requests.get(president_link)
    page = html.fromstring(res.content)
    bday = page.xpath("//span[@class='bday']/text()")
    return bday[0] if bday else None


def get_country_population(infobox):
    """
    extract the estimated population of a country
    from it's infobox. If more than one estimate
    exists, the first is taken (usually latest)
    :param infobox: lxml html element of infobox
    :return: population (int) or None of missing.
    """
    population_estimate = infobox.xpath("descendant::tr[descendant::*[contains(text(), 'Population')]]/following::tr[1]/td//text()[1]")
    if len(population_estimate) > 0:
        estimate_strings = [e for e in population_estimate[0].split(" ") if not e.isspace() if e]
        pop_num = clean_number(estimate_strings[0])
        assert pop_num
        return pop_num
    else:
        return None


def get_country_prime(infobox):
    """
    extract prime minister name, wiki link and
    birthday from infobox.
    :param infobox: lxml html element of infobox
    :return: tuple of name, link and bday, or None
    if missing from infobox.
    """
    # get prime minister and link if exist
    priminister_a = infobox.xpath("descendant::tr[descendant::*[contains(text(), 'Prime Minister')]][1]/td[1]//a[1]")
    if len(priminister_a) > 0:
        name = normalize_text(priminister_a[0].attrib['title'])
        link = priminister_a[0].attrib['href']
        bday = get_pres_prime_bday(WIKIPEDIA_BASE_URL + link)
        return name, link, bday
    else:
        return None, None, None


def get_country_president(infobox):
    """
    extract president name, wiki link and
    birthday from infobox.
    :param infobox: lxml html element of infobox
    :return: tuple of name, link and bday or None
    if missing from infobox.
    """
    president_a = infobox.xpath("descendant::tr[descendant::*[text()='President']][1]//td[1]//a[1]")
    if len(president_a) > 0:
        name = normalize_text(president_a[0].attrib['title'])
        link = president_a[0].attrib['href']
        bday = get_pres_prime_bday(WIKIPEDIA_BASE_URL + link)
        return name, link, bday
    else:
        return None, None, None


def get_country_capital(infobox):
    """
    extract capital city and link to it's wiki
    page from infobox.
    :param infobox: lxml.html element of infobox
    :return: tuple of name and link
    """
    capital_a = infobox.xpath("descendant::tr[th[contains(text(), 'Capital')]][1]//a[not(contains(@class, 'external')) and not(contains(@href, 'endnote'))][1]")
    if len(capital_a) > 0:
        name = normalize_text(capital_a[0].attrib['title'])
        link = capital_a[0].attrib['href']
        return name, link
    else:
        return None, None


def get_country_area(infobox):
    """
    extract total area of country in square km
    from infobox.
    :param infobox: lxml.html element of infobox
    :return: area (int) or None if missing.
    """
    country_area = infobox.xpath("descendant::tr[contains(th//text(), 'Total')][1]/td[1]/text()[1]")
    area_strings = [a for a in country_area[0].split(" ") if not a.isspace() if a]
    if len(country_area) > 0:
        return int(clean_number(area_strings[0]))
    else:
        return None


def get_country_government(infobox):
    """
    extract government types from the country info
    box. There can be more than one, so a dict is returned
    with types and links to wikipages of the types.
    :param infobox: lxml.html element of the infobox.
    :return: dictionary gov_type_name -> gove_type_wiki_link
    """
    government_dict = {}  # maps government types to wiki pages repersenting them
    government_items = infobox.xpath("descendant::tr[descendant::a[contains(text(), 'Government')] or descendant::th[contains(text(), 'Government')]]/td//node()")
    for gov_i in government_items:
        if isinstance(gov_i, html.HtmlElement) and gov_i.tag == 'a':  # only take the de jure government types
            if ('title' in gov_i.attrib) and (gov_i.attrib['title'] == "De jure" or gov_i.attrib['title'] == "De facto"):
                break
            elif 'href' in gov_i.attrib and 'title' in gov_i.attrib:  # only if it has a link
                government_dict[normalize_text(gov_i.attrib['title'])] = gov_i.attrib['href']
        elif isinstance(gov_i, lxml.etree._ElementUnicodeResult):
            if ('de jure' in gov_i) or ('De jure' in gov_i) or ('De facto' in gov_i) or ('de facto' in gov_i):
                break
    return government_dict


def get_country_infobox(country_link):
    res = requests.get(country_link)
    page = html.fromstring(res.content)
    info_box = page.xpath("//table[contains(@class, 'infobox')][1]")
    assert (len(info_box) > 0)
    return info_box[0]


def get_country_info(country_link):
    """
    return dict of information about country, including:
    - prime minister name + link to wiki page + bday
    - president name + link to wiki page + bday
    - area of country
    - population
    - types of government (can match a number of types)
    - capital city
    :param country_link: link to a wikipedia page of a country
    :return: dict of listed information about country. None in
    place of missing data
    """
    # get the page infobox
    info_box = get_country_infobox(country_link)

    # prepare dictionary for data
    info_dict = {'prime_minister_name' : None,
                 'prime_minister_link' : None,
                 'president_name': None,
                 'president_link': None,
                 'area': None,
                 'population': None,
                 'government_types': None,
                 'capital_city': None,
                 'capital_city_link': None
                 }

    # get president name and link if exist
    pres_name, pres_link, pres_bday = get_country_president(info_box)
    if pres_name:
        info_dict['president_name'] = pres_name
        info_dict['president_link'] = pres_link
        info_dict['president_bday'] = pres_bday

    # get prime minister and link if exist
    prime_name, prime_link, prime_bday = get_country_prime(info_box)
    if prime_name:
        info_dict['prime_minister_name'] = prime_name
        info_dict['prime_minister_link'] = prime_link
        info_dict['prime_minister_bday'] = prime_bday

    # get capital city
    capital, capital_link = get_country_capital(info_box)
    if capital:
        info_dict['capital_city'] = capital
        info_dict['capital_city_link'] = capital_link


    # get country area
    country_area = get_country_area(info_box)
    if country_area:
        info_dict['area'] = country_area


    # get country population estimate
    population_estimate = get_country_population(info_box)
    if population_estimate:
        info_dict['population'] = population_estimate


    # get government types - there can be many!
    government_dict = get_country_government(info_box)
    info_dict['government_types'] = government_dict if len(government_dict) else None

    # add country link
    info_dict['country_link'] = country_link
    return info_dict


def build_ontology_from_info(country_info):
    """
    creates an onotology with the following relations:
        <person> <president_of> <country>
        <person> <prime_minister_of> <country>
        <country> <population> <number>
        <country> <area> <number>
        <government_type> <is_government_type_of> <country>
        <country> <has_government_type> <government_type>
        <city> <capital_of> <country>
        <person> <birthday> <date>
        <name> <is_a> <country>
        <name> <is_a> <city>
        <name> <is_a> <person>
        <person> <job> <president / prime_minister>
    :param country_info: dictionary containing all relevant information
    for each country in the world
    :return: rdflib graph of the ontology.
    """
    ontology_graph = rdflib.Graph()

    # basic entities for use in relations
    country = URIRef('https://en.wikipedia.org/wiki/Country')
    person = URIRef('https://en.wikipedia.org/wiki/Person')
    job = URIRef('https://en.wikipedia.org/wiki/Job')
    city = URIRef("https://en.wikipedia.org/wiki/City")
    president = URIRef("https://en.wikipedia.org/wiki/President")
    prime_minister = URIRef("https://en.wikipedia.org/wiki/Prime_minister")
    capital = URIRef("https://en.wikipedia.org/wiki/Capital_city")
    population = URIRef("https://en.wikipedia.org/wiki/Population")
    area = URIRef("https://en.wikipedia.org/wiki/Area")
    is_a = URIRef("https://en.wikipedia.org/wiki/Is-a")
    government_type = URIRef("https://en.wikipedia.org/wiki/Government")
    type_to_country = URIRef("http://example.org/government_to_country")
    birthday = URIRef("https://en.wikipedia.org/wiki/Birthday")

    # add relations for each country
    for country_name, cdata in country_info.items():
        clink = URIRef(cdata['country_link'])
        # add to is_a country relation
        ontology_graph.add((clink, is_a, country))

        # add capital city to ontology relations
        if cdata['capital_city_link']:
            capital_link = URIRef(WIKIPEDIA_BASE_URL + cdata['capital_city_link'])
            ontology_graph.add((capital_link, is_a, city))  # add to is_a city
            ontology_graph.add((capital_link, capital, clink))

        # add the prime minister
        if cdata['prime_minister_link']:
            pmlink = URIRef(WIKIPEDIA_BASE_URL + cdata['prime_minister_link'])
            ontology_graph.add((pmlink, is_a, person))  # make person
            ontology_graph.add((pmlink, prime_minister, clink))  # make prime
            ontology_graph.add((pmlink, job, prime_minister))
            # add birthday
            if cdata['prime_minister_bday']:
                prime_bday = Literal(cdata['prime_minister_bday'], datatype=XSD.date)
                ontology_graph.add((pmlink, birthday, prime_bday))

        # add the president
        if cdata['president_link']:
            prlink = URIRef(WIKIPEDIA_BASE_URL + cdata['president_link'])
            ontology_graph.add((prlink, is_a, person))
            ontology_graph.add((prlink, president, clink))
            ontology_graph.add((prlink, job, president))
            # add birthday
            if cdata['president_bday']:
                pres_bday = Literal(cdata['president_bday'], datatype=XSD.date)
                ontology_graph.add((prlink, birthday, pres_bday))

        # add the population
        if cdata['population']:
            ontology_graph.add((clink, population, Literal(cdata['population'], datatype=XSD.positiveInteger)))

        # add the area
        if cdata['area']:
            ontology_graph.add((clink, area, Literal(cdata['area'], datatype=XSD.positiveInteger)))

        # add government types
        if cdata['government_types']:
            for gt in cdata['government_types'].values():
                glink = URIRef(WIKIPEDIA_BASE_URL + gt)
                ontology_graph.add((clink, government_type, glink))  # country to type
                ontology_graph.add((glink, type_to_country, clink))  # type to country
    return ontology_graph


def main_build_ontology(out_path):
    # get links to country wikipedia pages
    country_links = get_country_links(COUNTRY_WIKI_URL)

    # get details about each country
    country_data = {}
    for country, link in country_links.items():
        print('working on: ', country)
        full_link = WIKIPEDIA_BASE_URL + link
        cinfo = get_country_info(full_link)
        country_data[country] = cinfo

    # create the ontology and save it
    ontology = build_ontology_from_info(country_data)
    ontology.serialize(out_path, format='nt')
    return


# ---------------------------------------------#
# ------FUNCTIONS FOR PARSING QUERIES----------#
# ---------------------------------------------#

def normalize_text(text):
    """
    strip, replace spaces with underscores, convert to lower case
    :param text: any string
    :return: normalized text
    """
    striped = '_'.join(re.split("\s+", text.strip().lower().replace("-", "_")))

    return ''.join([c for c in striped if (c.isalpha() or c == "_")])


def extract_president_query_country(nlp_query):
    country = re.split("president(\s+)of(\s+)", nlp_query)[-1].replace("?", "")
    return normalize_text(country)


def extract_prime_query_country(nlp_query):
    country = re.split("prime(\s+)minister(\s+)of(\s+)", nlp_query)[-1].replace("?", "")
    return normalize_text(country)


def extract_population_country(nlp_query):
    country = re.split("population(\s+)of(\s+)", nlp_query)[-1]
    return normalize_text(country)


def extract_area_country(nlp_query):
    country = re.split("area(\s+)of(\s+)", nlp_query)[-1]
    return normalize_text(country)


def extract_government_country(nlp_query):
    country = re.split("government(\s+)of(\s+)", nlp_query)[-1]
    return normalize_text(country)


def extract_capital_country(nlp_query):
    country = re.split("capital(\s+)of(\s+)", nlp_query)[-1]
    return normalize_text(country)


def extract_birthday_country(nlp_query):
    aug_query = nlp_query.replace("born", "").replace("?", "")
    country = re.split("of(\s+)", aug_query)[-1]
    return normalize_text(country)


def extract_who_is_person(nlp_query):
    return normalize_text(re.sub("Who(\s+)is(\s+)", "", nlp_query).replace("?", ""))


def parse_query(query):
    # who is the president of <country>
    if re.match(presi_re, query):
        country = extract_president_query_country(query)
        return "presi", country

    # who is the prime minister of <country>
    elif re.match(prime_re, query):
        country = extract_prime_query_country(query)
        return "prime", country

    # what is the population of <country>
    elif re.match(population_re, query):
        country = extract_population_country(query)
        return "popul", country

    # what is the area of <country>
    elif re.match(area_re, query):
        country = extract_area_country(query)
        return "area", country

    # what is the government of <country>
    elif re.match(govern_re, query):
        country = extract_government_country(query)
        return "gov", country

    # what is the capital of <country>
    elif re.match(capital_re, query):
        country = extract_capital_country(query)
        return "capital", country

    # what is the birthday of president of <country>
    elif re.match(presi_bday_re, query):
        country = extract_birthday_country(query)
        return "presi_bday", country

    # what is the birthday of prime minister of <country>
    elif re.match(prime_bday_re, query):
        country = extract_birthday_country(query)
        return "prime_bday", country

    # who is <person>
    elif re.match(who_re, query):
        person = extract_who_is_person(query)
        return "who", person

    # no match
    else:
        return None, None


def get_response_string(query_key, result):
    if query_key == "popul":
        return "{:,}".format(int(result[0][0]))

    elif query_key == "area":
        return "{:,} km2".format(int(result[0][0]))

    elif query_key in {'prime', 'presi', 'capital'}:
        rem_base = result[0][0].replace(WIKIPEDIA_BASE_URL, "").replace("/wiki/", "")
        return ' '.join([p.capitalize() for p in rem_base.split("_")])

    elif query_key in {'presi_bday', 'prime_bday'}:
        return result[0][0]

    elif query_key == "gov":
        type_list = []
        for r in result:
            clean_type = ' '.join([p.capitalize() for p in r[0].replace(WIKIPEDIA_BASE_URL, "").replace("/wiki/", "").split("_")])
            type_list.append(clean_type)
        return ", ".join(type_list)

    elif query_key == "who":
        res_list = []
        for r in result:
            pos = ' '.join(r[0].replace(WIKIPEDIA_BASE_URL, "").replace("/wiki/", "").split("_"))
            country = ' '.join(r[1].replace(WIKIPEDIA_BASE_URL, "").replace("/wiki/", "").split("_"))
            res_list.append(pos + " of " + country)
        return ", ".join(res_list)
    return

if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser(description='NLP ontology construction and queries.')
    parser.add_argument("func", type=str)
    parser.add_argument("query_path", type=str)
    args = parser.parse_args()

    if args.func == "create":
        main_build_ontology(args.query_path)

    elif args.func == "question":
        # make sure ontology file exists in current directory
        if os.path.isfile("ontology.nt"):
            # load the ontology file
            country_ont = rdflib.Graph()
            country_ont.parse("ontology.nt", format='nt')

            # parse the query
            query_key, query_arg = parse_query(args.query_path)
            if query_key is None:
                print("unrecognized query.")
                exit(1)

            # create query from format
            required_query = query_formats[query_key] % (query_arg)

            # execute query
            query_res = list(country_ont.query(required_query))

            # format query result as answer string
            if query_res:
                response = get_response_string(query_key, query_res)
                print(response)
            else:
                print("no results found.")

        else:
            print("Error: ontology.nt file was not found in current working directory.")
            exit(1)
    else:
        print("unrecognized function")
        exit(1)
