import json

from sln import Parser

with open("./test.sln", 'r') as rf:
    sln_text = rf.read()

# raw parse, the atoms are Symbol objects and containers are tuples
results = Parser(sln_text).parse()
print(results)

# parse to strings and atoms as strings
str_results = Parser(sln_text).parse_to_string()
print(str_results)

json_results = json.dumps(str_results)
print(json_results)
