class _TemplateMetaclass(type):
    def __init__(cls, name, bases, dct):
        super(_TemplateMetaclass, cls).__init__(name, bases, dct)

# From 3.7.7. test_logging.
# In 3.7 CALL_METHOD is introduced and used in logging.getLoggerClass
import logging
class MyLogger(logging.getLoggerClass()):
    pass
