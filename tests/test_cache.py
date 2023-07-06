from cache_redis.cache import add_rate, show_reviewers, check_exists_rate, get_rate, remove_rate


def test_rate_op(setup_and_teardown_cache, monkeypatch, redis_session):
    monkeypatch.setattr('cache_redis.cache.r', redis_session)
    added = add_rate('likes', 1, 'foo@example.com')
    assert added == 1
    added = add_rate('likes', 1, 'foo@example.com')
    assert added == 0
    added = add_rate('likes', 2, 'foo@example.com')
    assert added == 1
    add_rate('likes', 1, 'too@example.com')
    likes = show_reviewers('likes', 1)
    assert likes == {'foo@example.com', 'too@example.com'}
    flag = check_exists_rate('likes', 1, 'foo@example.com')
    assert flag
    flag = check_exists_rate('likes', 1, 'do@example.com')
    assert not flag
    length = get_rate('likes', 1)
    assert length == 2
    remove_rate('likes', 1, 'foo@example.com')
    length = get_rate('likes', 1)
    assert length == 1
    remove_rate('likes', 1, 'too@example.com')
    length = get_rate('likes', 1)
    assert length == 0
