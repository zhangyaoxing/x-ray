def gen_mock_write_output(item):
    """Generate a mock _write_output function for testing.

    Args:
        item: The item object whose _cache will be captured

    Returns:
        tuple: (output list, mock function)
            - output: A list that will collect all written data
            - mock function: A function that captures item._cache into output
    """
    output = []

    def _mock_write_output_internal():
        """Mock _write_output that captures cache instead of writing to file."""
        nonlocal output
        cache = item._cache
        if cache is None:
            return
        if isinstance(cache, list):
            for cache_item in cache:
                output.append(cache_item.copy())
        else:
            output.append(cache.copy())

    return output, _mock_write_output_internal
