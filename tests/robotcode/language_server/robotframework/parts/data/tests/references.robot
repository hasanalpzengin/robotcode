*** Settings ***
Library         Collections
#               ^^^^^^^^^^^ a builtin library
Library         ${CURDIR}/../lib/myvariables.py
#                 ^^^^^^  Variable in library import path
#                             ^^^^^^^^^^^^^^ a custom library with path
Variables       ${CURDIR}/../lib/myvariables.py
#                 ^^^^^^  Variable in variables import path
#                                ^^^^^^^^^^^^^^ a variable import
Resource        ${CURDIR}/../resources/firstresource.resource
#                 ^^^^^^  Variable in resource import path
Library         alibrary    a_param=from hello    WITH NAME    lib_hello
##               ^^^^^^^^ a custom library  # TODO: flaky
Library         alibrary    a_param=${LIB_ARG}    WITH NAME    lib_var
#                                     ^^^^^^^  Variable in library params
##               ^^^^^^^^ a same custom library  # TODO: flaky
Suite Setup    BuiltIn.Log To Console    hi from suite setup
#                      ^^^^^^^^^^^^^^  suite fixture keyword call with namespace
Test Setup    Log To Console    hi from test setup
#             ^^^^^^^^^^^^^^  test fixture keyword call with namespace

*** Variables ***
${a var}    hello
# ^^^^^ simple variable
${LIB_ARG}    from lib
# ^^^^^^^ another simple var
${bananas}    apples
${🧨🧨}    🎉🎉
# ^^^^^ a var with emoji

*** Test Cases ***
first
    [Setup]    Log To Console    hi ${a var}
#              ^^^^^^^^^^^^^^  fixture keyword call
    [Teardown]    BuiltIn.Log To Console    hi ${a var}
#                         ^^^^^^^^^^^^^^  fixture keyword call with namespace
    Log    Hi ${a var}
#   ^^^  simple keyword call
    Log To Console    hi ${a var}
#   ^^^^^^^^^^^^^^  multiple references
    BuiltIn.Log To Console    hi ${a var}
#           ^^^^^^^^^^^^^^  multiple references with namespace
#                                  ^^^^^  multiple variables
    Log    ${A_VAR_FROM_RESOURE}
#            ^^^^^^^^^^^^^^^^^^ a var from resource

second
    [Template]    Log To Console
#                 ^^^^^^^^^^^^^^  template keyword
    Hi
    There

third
    [Template]    BuiltIn.Log To Console
#                         ^^^^^^^^^^^^^^  template keyword with namespace
    Hi
    There

forth
    ${result}    lib_hello.A Library Keyword
#     ^^^^^^    Keyword assignement
    Should Be Equal    ${result}   from hello
    ${result}=    lib_var.A Library Keyword
#    ^^^^^^^    Keyword reassignment with equals sign
    Should Be Equal    ${result}   ${LIB_ARG}
#                        ^^^^^^    Keyword variable reference


fifth
    [Setup]    do something test setup inner
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword in setup
    [Teardown]    do something test teardown inner
#                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword in teardown
    do something    cool
    do something cool from keyword
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword

    add 2 coins to pocket
#   ^^^^^^^^^^^^^^^^^^^^^  Embedded keyword with regex only numbers

    add 22134 coins to pocket
#   ^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword with regex only numbers
    add milk and coins to my bag
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword with regex a to z an space

    do add ${bananas} and to my bag
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword with variable

    do add ${🧨🧨} and to my bag
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword with emojii variable

    add bananas to pocket
#   ^^^^^^^^^^^^^^^^^^^^^  Ambiguous Embedded keyword with regex a to z
    add bananas to pocket    # robotcode: ignore
#   ^^^^^^^^^^^^^^^^^^^^^  Invalid Embedded keyword with regex a to z ignored
    add bananas and apples to pocket
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword with regex a to z and space

    add bananas and apples to 🦼🛹🛼
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword with emoji


sixth
    🤖🤖  🐓=🥴🥶
#   ^^^^ a keyword with emoji
    firstresource.🤖🤖  🐓=${🧨🧨}    🧟‍♂️🛃🫅🏿👸🏿=${🧨🧨}+${🧨🧨}  #  test
#   ^^^^^^^^^^^^^^^^^^  a keyword with namespace and emoji
#                           ^^^  a variable with emoji


seventh
    firstresource.a keyword with args    a=2    a long name=99    a_short_name=342
#                                        ^  short keyword argument
#                                               ^^^^^^^^^^^  keyword argument with spaces
#                                                                 ^^^^^^^^^^^^  another keyword argument
    Log    message=123

*** Keywords ***
do something ${type}
    do something     ${type}

do something
    [Arguments]    ${type}
    Log    done ${type}

add ${number:[0-9]+} coins to ${thing}
#^^  Embedded keyword
#     ^^^^^^  Embedded keyword
    Log    added ${number} coins to ${thing}
#                  ^^^^^^ embedded argument usage
#                                     ^^^^^ embedded argument usage

add ${what:[a-zA-Z]+} to ${thing}
#^^  Embedded keyword
    Log    this is duplicated
    Log    added ${what} to ${thing}

add ${what:[a-zA-Z]+} to ${thing}
#^^  Embedded keyword
    Log    added ${what} coins to ${thing}

add ${what:[a-zA-Z ]+} to ${thing}
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  Embedded keyword
    Log    added ${what} coins to ${thing}

do add ${bananas} and to my bag
#^^  Embedded keyword
    Log    ${bananas}

a keyword with params
    [Arguments]    ${A VAR}=${A VAR}
#                    ^^^^^ another argument
#                             ^^^^^ a default value
    Log    ${tt}
#            ^^ argument usage
    Log    ${A VAR}
#            ^^^^^ argument usage

another keyword with params
    [Arguments]    ${tt}    ${A VAR}=${A VAR}
#                    ^^ an argument
#                             ^^^^^ another argument
#                                      ^^^^^ a default value
    Log    ${tt}
#            ^^ argument usage
    Log    ${A VAR}
#            ^^^^^ argument usage

again a keyword with params
    [Arguments]    ${a}    ${b}=${a}
#                    ^ an argument
#                            ^ another argument
#                                 ^ argument usage in argument
    Log    ${a}
#            ^ argument usage
    Log    ${b}
#            ^ argument usage

a keyword with variables in doc, timeout and tags
    [Documentation]    a keyword with parameters ${a var} and ${a}
#                                                  ^^^^^ a global var in doc
#                                                               ^ an argument in doc
    [Timeout]    ${a}
#                  ^ an argument in timeout
    [Tags]    ${a}   ${a var}    1234
#               ^ an argument in tags
#                      ^^^^^ an argument in tags
    [Arguments]    ${a}    ${b}=${a}
    Log    ${a}
    Log    ${b}

a keyword with variables in doc, timeout and tags with args first
    ${a}  Set Variable  1
    [Arguments]    ${a}    ${b}=${a}
    [Documentation]    a keyword with parameters ${a var} and ${a}
#                                                  ^^^^^ a global var in doc
#                                                               ^ an argument in doc
    [Timeout]    ${a}
#                  ^ an argument in timeout
    [Tags]    ${a}   ${a var}    1234
#               ^ an argument in tags
#                      ^^^^^ an argument in tags
    Log    ${a}
    Log    ${b}

    ${result}    Set Variable    1
    [Teardown]    Log    ${result}
#                          ^^^^^^ a local variable in teardown

a keyword with a while loop
    VAR    ${counter}    ${0}
#            ^^^^^^^ counter variable
    WHILE    True    limit=2s
        Log To Console    ${counter}
#                           ^^^^^^^ counter variable usage
        VAR    ${counter}    ${counter+1}
#                ^^^^^^^ counter variable assignment
#                              ^^^^^^^ another counter variable usage
    END

a keyword with python expressions
    [Documentation]    Escape pipe from input string:
    ...    - if surunded by spaces
    ...    - if it is the ending character
    [Arguments]    ${val}
#                   ^^^^ an argument
    VAR    ${output}    ${{ re.sub(r' \|$', ' \|', $val) }}
#                                                   ^^^ an argument usage
#            ^^^^^^ local variable definition
    VAR    ${output}    ${{ re.sub(r' \| ', ' \| ', $output) }}
#            ^^^^^^ local variable assignment
    RETURN    ${output}
#               ^^^^^^ local variable usage

a keyword with a while loop and variable in while options
    [Documentation]    Showing argument not used but should not
    [Arguments]    ${retries}
#                    ^^^^^^^ an argument
    WHILE    ${True}    limit=${retries}
#                               ^^^^^^^ argument usage in while option
        No Operation
    END

a keyword with VAR in condition
    [Documentation]    Unused variable error and collapsing error
    [Arguments]    ${arg}
    IF    $arg == 1
        VAR    ${my var}    foo
#                ^^^^^^ variable definition in if block
    ELSE
        VAR    ${my var}    bar
#                ^^^^^^ variable definition in else block
    END
    RETURN    ${my var}
#               ^^^^^^ variable usage

a keyword with while and expression variable
    [Documentation]    Showing argument not used but should not
    [Arguments]    ${count}    ${retries}
#                    ^^^^^^^ an argument
    VAR  ${i}  ${0}
    WHILE    $i < $count    limit=${retries}
#             ^ local variable usage
#                  ^^^^^ argument usage
#                                   ^^^^^^^ argument usage in while option
        No Operation
    END

try except with options
    ${beginning}=    Set Variable    1
    ${MATCH TYPE}     Set Variable  regexp

    TRY
        Some Keyword
    EXCEPT    ValueError:    ${beginning}    type=start
#                              ^^^^^^^^^ local variable usage
        Error Handler
    END

    TRY
        Some Keyword
    EXCEPT    ValueError: .*    type=${MATCH TYPE}
#                                      ^^^^^^^^^^ variable in option
        Error Handler 1
    EXCEPT    [Ee]rror \\d+ occurred    type=Regexp    # Backslash needs to be escaped.
        Error Handler 2
    END
