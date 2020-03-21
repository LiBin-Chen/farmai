#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""程序

@description
    说明
"""

test_dict = [{'a': 2, 'b': 2}, {'a': 4, 'b': 1}, {'a': 8, 'b': 3}, {'a': 0, 'b': 2}, {'a': 1, 'b': 1}]


# from operator import itemgetter
#
# print(sorted(test_dict, key=itemgetter('a')))
test_dict.sort(key=lambda x:x['a'])
print(test_dict)