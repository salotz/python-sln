from sln import Parser

with open("./test.sln", 'r') as rf:

    parser = Parser(rf.read())

results = parser.parse()

print(results)
