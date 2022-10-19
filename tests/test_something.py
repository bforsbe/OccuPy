def test_something_super_simple():
    assert True is True  # woah


def test_using_a_reusable_fixture(something_to_resuse):
    assert something_to_resuse == 1
