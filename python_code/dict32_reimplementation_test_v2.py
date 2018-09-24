import random
import argparse
import string
import json

from common import EMPTY
from dictinfo32 import dictobject, dump_py_dict
from dict32_reimplementation import PyDictReimplementation, dump_reimpl_dict
from js_reimplementation_interface import Dict32JsImpl, AlmostPythonDictRecyclingJsImpl, AlmostPythonDictNoRecyclingJsImpl
import hash_chapter3_class_impl


def dict_factory(pairs):
    # quick&dirty
    def to_string(x):
        return json.dumps(x) if x is not None else "None"
    d = eval("{" + ", ".join("{}:{}".format(to_string(k), to_string(v)) for [k, v] in pairs) + "}")
    dump = dump_py_dict(dictobject(d))
    print("Initial dict size", len(dump[0]))
    return d


IMPLEMENTATIONS = {
    "dict32_actual": (dict_factory, lambda d: dump_py_dict(dictobject(d))),
    "dict32_reimpl_py": (PyDictReimplementation, dump_reimpl_dict),
    "dict32_reimpl_js": (Dict32JsImpl, dump_reimpl_dict),

    "almost_python_dict_recycling_py": (hash_chapter3_class_impl.AlmostPythonDictImplementationRecycling, dump_reimpl_dict),
    "almost_python_dict_no_recycling_py": (hash_chapter3_class_impl.AlmostPythonDictImplementationNoRecycling, dump_reimpl_dict),
    "almost_python_dict_recycling_js": (AlmostPythonDictRecyclingJsImpl, dump_reimpl_dict),
    "almost_python_dict_no_recycling_js": (AlmostPythonDictNoRecyclingJsImpl, dump_reimpl_dict),
}

_unicode_chars = string.ascii_uppercase + string.digits + "йцукенгшщзхъфывапролджэячсмитьбю"


def generate_random_unicode(str_len):
    # FROM: https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
    return ''.join(random.choice(_unicode_chars) for _ in range(str_len))


def verify_same(d, dump_d_func, dreimpl, dump_dreimpl_func):
    dump_d = dump_d_func(d)
    dump_reimpl = dump_dreimpl_func(dreimpl)

    if dump_d != dump_reimpl:
        hashes_orig, keys_orig, values_orig, fill_orig, used_orig = dump_d
        hashes_new, keys_new, values_new, fill_new, used_new = dump_reimpl
        print("ORIG SIZE", len(hashes_orig))
        print("NEW SIZE", len(hashes_new))
        print("ORIG fill/used: ", fill_orig, used_orig)
        print("NEW fill/used: ", fill_new, used_new)
        if len(hashes_orig) == len(hashes_new):
            size = len(hashes_orig)
            print("NEW | ORIG")
            for i in range(size):
                if hashes_new[i] is not EMPTY or hashes_orig[i] is not EMPTY:
                    print(i, " " * 3,
                          hashes_new[i], keys_new[i], values_new[i], " " * 3,
                          hashes_orig[i], keys_orig[i], values_orig[i])

    assert dump_d == dump_reimpl


class IntKeyValueFactory(object):
    def __init__(self, n_inserts):
        self.n_inserts = n_inserts
        self._insert_count = 0
        self._key_range = list(range(n_inserts))

    def generate_key(self):
        return random.choice(self._key_range)

    def generate_value(self):
        self._insert_count += 1
        return self._insert_count


# TODO: long ints
class AllKeyValueFactory(object):
    def __init__(self, n_inserts, int_chance=0.1, long_chance=0.1, len0_chance=0.01, len1_chance=0.1, len2_chance=0.3, len3_chance=0.2, len_random_chance=0.17):
        self.int_pbf = int_chance
        self.long_pbf = self.int_pbf + long_chance
        self.len0_pbf = self.int_pbf + len0_chance
        self.len1_pbf = self.len0_pbf + len1_chance
        self.len2_pbf = self.len1_pbf + len2_chance
        self.len3_pbf = self.len2_pbf + len3_chance
        self.len_random_pbf = self.len3_pbf + len_random_chance
        assert 0.0 <= self.len3_pbf <= 1.0

        half_range = int(n_inserts / 2)
        self._int_range = [i - half_range for i in range(2 * half_range)]

    def _generate_obj(self):
        r = random.random()
        if r <= self.int_pbf:
            return random.choice(self._int_range)
        if r <= self.long_pbf:
            sign = "-" if random.random() < 0.5 else ""
            first_digit = random.choice("123456789")
            return sign + first_digit + ''.join(random.choice("0123456789") for _ in range(random.randint(20, 50)))
        if r <= self.len0_pbf:
            return ""
        if r <= self.len1_pbf:
            return generate_random_unicode(1)
        if r <= self.len2_pbf:
            return generate_random_unicode(2)
        if r <= self.len3_pbf:
            return generate_random_unicode(3)
        if r <= self.len_random_pbf:
            return generate_random_unicode(random.randint(4, 25))
        return None

    def generate_key(self):
        return self._generate_obj()

    def generate_value(self):
        return self._generate_obj()


def run(ref_impl_factory, ref_impl_dump, test_impl_factory, test_impl_dump, n_inserts, extra_checks, key_value_factory, initial_state):
    SINGLE_REMOVE_CHANCE = 0.3
    MASS_REMOVE_CHANCE = 0.002
    MASS_REMOVE_COEFF = 0.8

    removed = set()
    d = ref_impl_factory(initial_state)
    dreimpl = test_impl_factory(initial_state)
    print("Starting test")

    for i in range(n_inserts):
        should_remove = (random.random() < SINGLE_REMOVE_CHANCE)
        if should_remove and d and d.keys():  # TODO: ugly, written while on a plane
            to_remove = random.choice(list(d.keys()))
            print("Removing {}".format(to_remove))
            del d[to_remove]
            del dreimpl[to_remove]
            print(d)
            verify_same(d, ref_impl_dump, dreimpl, test_impl_dump)
            removed.add(to_remove)

        should_mass_remove = (random.random() < MASS_REMOVE_CHANCE)
        if should_mass_remove and len(d) > 10:
            to_remove_list = random.sample(list(d.keys()), int(MASS_REMOVE_COEFF * len(d)))
            print("Mass-Removing {} elements".format(len(to_remove_list)))
            for k in to_remove_list:
                del d[k]
                del dreimpl[k]
                removed.add(k)

        if extra_checks:
            for k in d.keys():
                assert d[k] == dreimpl[k]

            for r in removed:
                try:
                    dreimpl[r]
                    assert False
                except KeyError:
                    pass

        key_to_insert = key_value_factory.generate_key()
        value_to_insert = key_value_factory.generate_value()
        _keys_set = getattr(d, '_keys_set', None)
        # TODO: ugly code written on a plane
        # TODO: properly implement in/not in when I land
        if _keys_set is not None:
            key_present = key_to_insert in _keys_set
        else:
            key_present = key_to_insert in d

        if not key_present:
            print("Inserting ({key}, {value})".format(key=key_to_insert, value=value_to_insert))
            try:
                dreimpl[key_to_insert]
                assert False
            except KeyError:
                pass
        else:
            print("Replacing ({key}, {value1}) with ({key}, {value2})".format(key=key_to_insert, value1=d[key_to_insert], value2=value_to_insert))
        removed.discard(key_to_insert)
        d[key_to_insert] = value_to_insert
        dreimpl[key_to_insert] = value_to_insert
        print(d)
        verify_same(d, ref_impl_dump, dreimpl, test_impl_dump)
        assert dreimpl[key_to_insert] == value_to_insert


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stress-test dict-like reimplementations')
    parser.add_argument('--reference-implementation', choices=IMPLEMENTATIONS.keys(), required=True)
    parser.add_argument('--test-implementation', choices=IMPLEMENTATIONS.keys(), required=True)
    parser.add_argument('--no-extra-getitem-checks', dest='extra_checks', action='store_false')
    parser.add_argument('--num-inserts',  type=int, default=500)
    parser.add_argument('--forever', action='store_true')
    parser.add_argument('--kv', choices=["numbers", "all"], required=True)
    parser.add_argument('--initial-size', type=int, default=-1)
    args = parser.parse_args()

    if args.kv == "numbers":
        kv_factory = IntKeyValueFactory(args.num_inserts)
    elif args.kv == "all":
        kv_factory = AllKeyValueFactory(args.num_inserts)

    ref_impl = IMPLEMENTATIONS[args.reference_implementation]
    test_impl = IMPLEMENTATIONS[args.test_implementation]

    def test_iteration():
        initial_size = args.initial_size if args.initial_size > 0 else random.randint(0, 100)
        initial_state = [(kv_factory.generate_key(), kv_factory.generate_value()) for _ in range(initial_size)]
        run(*(ref_impl + test_impl),
            n_inserts=args.num_inserts,
            extra_checks=args.extra_checks,
            key_value_factory=kv_factory,
            initial_state=initial_state)

    if args.forever:
        while True:
            test_iteration()
    else:
        test_iteration()
