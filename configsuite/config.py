import copy
import configsuite
import collections


from .schema import assert_valid_schema


class ConfigSuite(object):

    def __init__(self, raw_config, schema):
        assert_valid_schema(schema)
        self._raw_config = copy.deepcopy(raw_config)
        self._schema = copy.deepcopy(schema)
        self._valid = None
        self._errors = None
        self._snapshot = None

    @property
    def valid(self):
        self._ensure_validation()
        return self._valid

    @property
    def errors(self):
        self._ensure_validation()
        return self._errors

    @property
    def snapshot(self):
        if self._snapshot is None:
            self._snapshot = self._build_snapshot(
                    self._raw_config,
                    self._schema,
                    )

        return self._snapshot

    def _build_snapshot(self, config, schema):
        if config is None:
            return None

        data_type = schema[configsuite.MetaKeys.Type]
        if isinstance(data_type, configsuite.BasicType):
            return config
        elif data_type == configsuite.types.Dict:
            content_schema = schema[configsuite.MetaKeys.Content]
            dict_name = data_type.name
            dict_keys = content_schema.keys()
            dict_collection = collections.namedtuple(dict_name, dict_keys)

            return dict_collection(**{
                key: self._build_snapshot(config.get(key), content_schema[key])
                for key in content_schema
            })
        elif data_type == configsuite.types.List:
            item_schema = schema[configsuite.MetaKeys.Content][configsuite.MetaKeys.Item]
            return tuple(map(
                lambda elem: self._build_snapshot(elem, item_schema),
                config
            ))
        else:
            msg = 'Encountered unknown type {} while building snapshot'
            raise TypeError(msg.format(str(data_type)))

    def _ensure_validation(self):
        if self._valid is None:
            validator = configsuite.Validator(self._schema)
            val_res = validator.validate(self._raw_config)
            self._valid = val_res.valid
            self._errors = val_res.errors