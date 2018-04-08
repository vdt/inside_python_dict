from common import DUMMY, NULL
from dict_reimpl_common import BaseDictImpl, Slot


class PyDictReimplementation(BaseDictImpl):
    START_SIZE = 8
    PERTURB_SHIFT = 5

    def __init__(self):
        BaseDictImpl.__init__(self)

    def __setitem__(self, key, value):
        fill_increased = self.insertdict(key, value)
        if fill_increased:
            self.fill += 1
        self.used += 1

        if self.fill * 3 >= len(self.slots) * 2:
            self.resize()

    def __delitem__(self, key):
        idx = self.lookdict(key)

        self.used -= 1
        self.slots[idx].key = DUMMY
        self.slots[idx].value = NULL

    def __getitem__(self, key):
        idx = self.lookdict(key)

        return self.slots[idx].value

    @staticmethod
    def signed_to_unsigned(hash_code):
        return 2**64 + hash_code if hash_code < 0 else hash_code

    def lookdict(self, key):
        hash_code = hash(key)
        perturb = self.signed_to_unsigned(hash_code)

        idx = hash_code % len(self.slots)
        while self.slots[idx].key is not NULL:
            if self.slots[idx].hash_code == hash_code and self.slots[idx].key == key:
                return idx

            idx = (idx * 5 + perturb + 1) % len(self.slots)
            perturb >>= self.PERTURB_SHIFT

        raise KeyError()

    def insertdict(self, key, value):
        hash_code = hash(key)
        perturb = self.signed_to_unsigned(hash_code)

        idx = hash_code % len(self.slots)
        target_idx = None
        while self.slots[idx].key is not NULL:
            if self.slots[idx].key == hash_code and self.slots[idx].key == key:
                target_idx = idx
                break
            if target_idx is None and self.slots[idx].key is DUMMY:
                target_idx = idx

            idx = (idx * 5 + perturb + 1) % len(self.slots)
            perturb >>= self.PERTURB_SHIFT

        if target_idx is None:
            target_idx = idx
        fill_increased = self.slots[target_idx].key is NULL

        self.slots[target_idx] = Slot(hash_code, key, value)

        return fill_increased

    def resize(self):
        # TODO: proper target size (it is sometimes 2, sometimes 4 -- based on used)
        quot = 4
        old_slots = self.slots
        new_size = self.find_optimal_size(quot)
        self.slots = [Slot() for _ in range(new_size)]

        for slot in old_slots:
            if slot.key is not NULL and slot.key is not DUMMY:
                self.insertdict(slot.key, slot.value)

        self.fill = self.used


def dump_py_reimpl_dict(d):
    return d.hashes, d.keys, d.values
