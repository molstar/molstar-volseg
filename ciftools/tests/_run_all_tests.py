import unittest

testmodules = [
    "byte_array",
    "delta",
    "fixed_point",
    "integer_packing",
    "interval_quantization",
    "run_length",
    "string_array",
    "_decoding",
    "_encoding",
]

suite = unittest.TestSuite()

for t in testmodules:
    try:
        # If the module defines a suite() function, call it to get the suite.
        mod = __import__(t, globals(), locals(), ["suite"])
        suitefn = getattr(mod, "suite")
        suite.addTest(suitefn())
    except (ImportError, AttributeError):
        # else, just load all the test cases from the module.
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

unittest.TextTestRunner().run(suite)
