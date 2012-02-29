def isprivate(method):
	return getattr(method, '__name__', method)[0] == '_'