def hash_fs(evt):
	print ((evt))
	print (frozenset(evt.items()))
	return hash(frozenset(evt.items()))

d = {"a": 1, "b": 2}
d1 = {"b": 2, "a": 1}

print( hash_fs(d))
print( hash_fs(d1))