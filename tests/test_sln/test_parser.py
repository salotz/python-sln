
from sln import Parser

def test_parse_to_string():

    cases = (
        ("""""", []),
        ("""single""", ['single']),
        ("""(single)""", [['single']]),
        ("""single;""", [['single']]),
        ("""list is one""", [['list', 'is', 'one']]),
        ("""(list is one)""", [['list', 'is', 'one']]),
        ("""(list (is one))""", [['list', ['is', 'one']]]),
        ("""list is \"one\"""", [['list', 'is', 'one']]),
        ("""list is 1""", [['list', 'is', 1]]),
        ("""1.0""", [1.0]),
        ("""list is None""", [['list', 'is', "None"]]),
        # TODO: this should work
        # ("""1,2,3""", [[1, 2, 3]]),
        (
            """
# comment here
    And continued here
list is one
            """,
            [['list', 'is', "one"]]
        ),
        (
            """
list
    is
    one
            """,
            [['list', 'is', "one"]]
        ),

        (
            """
list
    is one
            """,
            [['list', ['is', "one"]]]
        ),
        (
            """
list
    is
        one
            """,
            [['list', ['is', "one"]]]
        ),
        (
            """
list
    is
        one two
            """,
            [['list', ['is', ["one", "two"]]]]
        ),
        (
            """
list
    is
        one
        two
            """,
            [['list', ['is', "one", "two"]]]
        ),
    )

    for input, expected in cases:

        assert Parser(input).parse_to_string() == expected
