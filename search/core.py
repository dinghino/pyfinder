"""
Search API core module

Contains the main functions to perform a search.
"""
from search import utils, config, matchers


class SearchEngine:
    """
    Creates callable objects to perform lazy search in iterables of objects.
    The engine is customizable upon creation, and when the function is called.

    Search can be performed calling directly the object

        >>> search = SearchEngine(['attr_name'], limit=10)
        >>> result = search('john doe', [people])

    or through the search method

        >>> search_engine = SearchEngine(['attr_name'], limit=10)
        >>> result = search_engine.search('john doe')

    For actual documentation on the search functionality and parameters refer
    to the :any:`SearchEngine.search` method documentation.
    """

    def __init__(self, attributes=None, limit=-1,
                 threshold=config.THRESHOLD, weights=None,
                 matcher=matchers.lazy_match):
        self.attributes = attributes
        self.limit = limit
        self.threshold = threshold
        self.weights = weights
        self.matcher = matcher

        if attributes:
            if not self.weights or len(attributes) != len(weights):
                self.weights = utils.generate_weights(attributes)

    def __call__(self, query, dataset, attributes=None, limit=None,
                 threshold=None, weights=None, matcher=None):

        return self.search(
            query=query,
            dataset=dataset,
            attributes=attributes,
            limit=limit,
            threshold=threshold,
            weights=weights,
            matcher=matcher,
        )

    def select_results(self, matches, threshold, limit):
        """
        sort and trim the matches list, returning a list with the objects found
        """
        matches.sort(key=lambda m: m['rating'], reverse=True)
        if limit > 0:
            matches = matches[:limit]

        return [m['data'] for m in matches]

    def search(
            self, query, dataset, attributes=None, limit=None,
            threshold=None, weights=None, matcher=None):
        """
        Main function of the package, allows to do a fuzzy full-text search on
        the rows of the given `table` model, looking up the value
        on the given `attributes` list against the passed `query` string.

        Extra arguments allows customization on the search results (see below)

        .. note::
            Since this function implements the core functionality, it has the
            shortcut import

            >>> from search.core import search
            >>> from search import search

            Will have the same effect

        Arguments:
            query (str): String to search for
            attributes (list): The names of thetable columns to search into.
            dataset (iterable): iterable of `objects` to lookup. All objects
                in the dataset **must** have the specified attribute(s)
            limit (int): max number of results to return. if ``-1`` will return
                everything.
            threshold (float): paragon for validating match results.
            weights (list): matching `attributes` argument, describes the
                attributes weights. if not provided **or** if different length
                the weight will generated automatically, considering
                the index of the attribute name, reversed.

        Returns:
            list: A list containing ``[0:limit]`` resources from the given
            dataset, sorted by relevance.

        Raises:
            AttributeError: if one of the object does not have one of the given
                attribute(s).

        Example:
            Assuming a random number of items in the Item table, that defines
            `name`, `category`, `description`, `availability`, one can do:

            >>> from models import Item
            >>> from search import search
            >>> results = search('aweso', ['name', 'category'], Item.select())
            [
                <Item name: 'awesome item' cat: 'generic'>,
                <Item name: 'normal item', cat: 'awesome'>,
            ]

            Note that even though the category is a perfect match, it's ranked
            lower priority, so it comes after.

        """
        attributes = attributes or self.attributes
        weights = weights or self.weights
        limit = limit or self.limit
        threshold = threshold or self.threshold
        matcher = matcher or self.matcher

        if not attributes:
            raise ValueError('Missing attributes to search into.')

        if len(utils.tokenize(query)) == 0:
            # TODO: Raise custom exception QueryTooShort or something, since
            # when the query will be tokenized for matching it will generate
            # an empty set and won't have matches.
            return []

        def create_result(obj, match, score, attr):
            return {'data': obj, 'match': match, 'rating': score, 'attr': attr}

        if len(attributes) == 1:
            # perform a simplest search since we only have one attribute to
            # consider
            matches = []
            attr_name = attributes[0]
            for obj in dataset:
                match = matcher(query, getattr(obj, attr_name))
                if match >= threshold:
                    matches.append(create_result(obj, match, match, attr_name))

            return self.select_results(matches, threshold, limit)

        matches = []
        if not weights or len(weights) != len(attributes):
            # list of integers of the same length of `attributes` as in
            # [3, 2, 1] for attributes = ['a', 'b', 'c']
            weights = list(range(len(attributes), 0, -1))

        weights = utils.normalize(weights)
        weights = dict(zip(attributes, weights))

        for obj in dataset:
            partial_matches = []

            for attr in attributes:
                attrval = getattr(obj, attr)
                if len(attrval) == 0:
                    continue

                match = matcher(query, attrval)
                partial_matches.append({'attr': attr, 'match': match})

            # get the highest match found for each object after processing
            # all the attributes
            match = max(partial_matches, key=lambda m: m['match'])
            value = match['match']
            if value >= threshold:
                attr = match['attr']
                # Consider all the other matches when generating the actual
                # total value of matching for the rating. This helps when
                # we may have one object with two high match and one with
                # just one match.
                tot_value = value + sum([p['match'] for p in partial_matches])
                score = tot_value + weights[attr]
                result = create_result(obj, value, score, attr)
                matches.append(result)

        # adjust weights, setting the highest attribute weight to the attribute
        # that got more matches. This helps when searching through a keyword
        # attribute (like a `category`) that has a default lower weight but
        # that, if searched by name, should be higher in rating.
        # This is done by checking the amount of results for each attribute
        # and creating the weights from those values.
        adjusted_weights = utils.generate_weights_from_matches(matches)

        # adjust the rating adding the new weight for the attribute that
        # generated the highest match for each object.
        for match in matches:
            match['rating'] += adjusted_weights[match['attr']]

        return self.select_results(matches, threshold, limit)
