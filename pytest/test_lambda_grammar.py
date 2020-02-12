import re
from decompyle3.parsers.p37.lambda_expr import Python37LambdaParser

def test_grammar():
    p = Python37LambdaParser()
    # p.dump_grammar()
    p.check_grammar()

if __name__ == "__main__":
    test_grammar()
