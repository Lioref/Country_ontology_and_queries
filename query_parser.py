import re

# regular expressions for matching questions
presi_re = "^Who(\s+)is(\s+)the(\s+)president(\s+)of(\s+)(\w+)(\s*)(\w*)(\s*)(\?+)(\s*)$"
prime_re = "^Who(\s+)is(\s+)the(\s+)prime(\s+)minister(\s+)of(\s+)(\w+)(\s*)(\w*)(\s*)(\?+)(\s*)$"
population_re = "^What(\s+)is(\s+)the(\s+)population(\s+)of(\s+)(\w+)(\s*)(\w*)(\s*)(\?+)$"
area_re = "^What(\s+)is(\s+)the(\s+)area(\s+)of(\s+)(\w+)(\s*)(\?+)(\s*)$"
govern_re = "^What(\s+)is(\s+)the(\s+)government(\s+)of(\s+)(\w+)(\s*)(\?+)(\s*)$"
capital_re = "^What(\s+)is(\s+)the(\s+)capital(\s+)of(\s+)(\w+)(\s*)(\?+)(\s*)$"
presi_bday_re = "^When(\s+)was(\s+)the(\s+)president(\s+)of(\s+)(\w+)(\s+)born(\s*)(\?+)(\s*)$"
prime_bday_re = "^When(\s+)was(\s+)the(\s+)prime(\s+)minister(\s+)of(\s+)(\w+)(\s+)born(\s*)(\?+)(\s*)$"
who_re = "^Who(\s+)is(\s+)(\w+)(\s*)(\w*)(\s*)(\?+)(\s*)"

# clean the text, lower case, remove punctuation and trailing spaces etc.
def normalize_text(text):
    """
    strip, replace spaces with underscores, convert to lower case
    :param text: any string
    :return: normalized text
    """
    striped = '_'.join(re.split("\s+", text.strip().lower().replace("-", "_")))

    return ''.join([c for c in striped if (c.isalpha() or c == "_")])

# extraction functions
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


def main():
    example = "What is the population of Falkland Islands?"    
    country = extract_population_country(example)
    print("extracted country: {}".format(country))
    return

def main1():
    while True:
        query = input("\n> enter query: ")
        
        # exit if keyword is given
        if query == "quit":
            print("quiting...")
            break        
        
        # who is the president of <country>
        elif re.match(presi_re, query):
            country = extract_president_query_country(query)
            print("president query, country: {}".format(country))
        
        # who is the prime minister of <country>
        elif re.match(prime_re, query):
            country = extract_prime_query_country(query)
            print("prime minister query, country: {}".format(country))
        
        # what is the population of <country>
        elif re.match(population_re, query):
            country = extract_population_country(query)
            print("population query, country: {}".format(country))
        
        # what is the area of <country>
        elif re.match(area_re, query):
            country = extract_area_country(query)
            print("area query, country: {}".format(country))

        # what is the government of <country>
        elif re.match(govern_re, query):
            country = extract_government_country(query)
            print("government query, country: {}".format(country))

        # what is the capital of <country>
        elif re.match(capital_re, query):
            country = extract_capital_country(query)
            print("capital query, country: {}".format(country))

        # what is the birthday of president of <country>
        elif re.match(presi_bday_re, query):
            country = extract_birthday_country(query)
            print("president birthday query, country: {}".format(country))

        # what is the birthday of prime minister of <country>
        elif re.match(prime_bday_re, query):
            country = extract_birthday_country(query)
            print("prime minister birthday query, country: {}".format(country))

        # who is <person>
        elif re.match(who_re, query):
            person = extract_who_is_person(query)
            print("who is person query, person: {}".format(person))
        
        # no match
        else:
            print("unrecognized query.")
    return


if __name__ == '__main__':
    main1()
    print('Done.')