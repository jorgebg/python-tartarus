def lower_keys(collection):
	return dict((k.lower(), v) for k,v in collection.iteritems())
