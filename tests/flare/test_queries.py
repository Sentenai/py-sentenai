import pytest
import re

from hypothesis            import given, assume, example, settings
from hypothesis.strategies import text, dictionaries, booleans, integers, floats, lists, dates, datetimes, times, one_of
from sentenai              import stream, ast, span, select, delta, event, V, all_of, any_of
from sentenai.flare        import StreamPath, Cond, Span, Serial, Switch, Or, Select, Par

# Hypothesis Strategies
# ========================

def all_types():
    # FIXME: add times()
    return one_of(text(), booleans(), integers(), floats(), dates(), datetimes())

def all_multitypes():
    # FIXME: add lists of datetime types
    return one_of(
        lists(text(), min_size=1),
        lists(booleans(), min_size=1),
        lists(integers(), min_size=1),
        lists(floats(), min_size=1))
        #lists(dates(), min_size=1),
        #lists(datetimes(), min_size=1))


# Conditional Checks
# ========================

def assume_parsable(query):
    assume(type(query) == Cond)
    assume(type(ast(query)) == str)

def check_syntax_with_type(query, is_multitype=False):
    s = stream("")

    assume_parsable(s.foo == query)
    assume_parsable(s.foo >  query)
    assume_parsable(s.foo >= query)
    assume_parsable(s.foo <  query)
    assume_parsable(s.foo <= query)
    assume_parsable(s.foo != query)

    with pytest.raises(TypeError):
        s.foo >> query

    with pytest.raises(TypeError):
        s.foo << query

    if is_multitype:
        pass
        #assume_parsable(s.foo in query)
        #with pytest.raises(TypeError):
        #    s.foo in query
    else:
        with pytest.raises(TypeError):
            s.foo in query


# Conditional Tests
# ========================
with settings(max_examples=1000, min_satisfying_examples=500):
    @given(all_types())
    def test_conditionals(query):
        check_syntax_with_type(query)

    @given(all_multitypes())
    @example([])
    def test_multibools_conditionals(query):
        check_syntax_with_type(query, is_multitype=True)

    def test_text_wildcard():
        s = stream("")
        assume_parsable(s.foo == "test*")

    def test_text_regex():
        s = stream("")
        assume_parsable(s.foo == r'')

    # FIXME: include tests for geo
    # Geo                     -- Any geo
    # GeoDist (Double, Double) Double
    # InPoly (Double, Double) (Double, Double) (NonEmpty (Double, Double))


# Conditional Tests
# ========================

with settings(max_examples=1000, min_satisfying_examples=500):

    @given(all_types())
    def test_simple_spans(query):
        s1 = stream("1")
        s2 = stream("2")

        sp1 = span(s1.foo == query, s2.foo == query)
        sp2 = span(s1.foo == query, s2.foo == query, within=delta(days=2))

        assume(type(sp1) is Span)
        assume(type(sp2) is Span)


    @given(all_types(), all_types())
    def test_switch_construction(query1, query2):
        spike = event(V.foo == query1) >> event(V.bar < query2) >> event(V.baz != query1)
        assume(isinstance(spike, Switch))

        s = stream("1")
        assume(isinstance(s(spike), Switch))


    @given(all_types())
    def test_overloaded_ops(query):
        s1 = stream("1")
        s2 = stream("2")

        span1 = span(s2.foo == query)
        span2 = span(s1.foo == query)
        assume(type(span1) == Span and type(span2) == Span)

        assume(type(span1 & span2) == Span)
        assume(type(span1 | span2) == Or)
        assume(type(span1 >>span2) == Serial)


    @given(all_types(), all_types())
    def test_serial_construction(query1, query2):
        s1 = stream("1")
        s2 = stream("2")
        evt1 = event(V.foo == query1)
        evt2 = event(V.foo == query2)

        srl = span(s1(evt1)) \
             .then(s2(evt2), within=delta(days=5))

        assume(type(srl) is Serial)


    @given(all_types(), all_types())
    def test_par_construction(query1, query2):
        s1 = stream("1")
        s2 = stream("2")
        evt1 = event(V.foo == query1)
        evt2 = event(V.foo == query2)

        assume( isinstance(all_of(s1(evt1), s2(evt2)), Par) )
        assume( isinstance(any_of(s1(evt1), s2(evt2)), Par) )


