async def test_reg(mocker, get_stub_output_user, get_client, get_stub_user):
    mocker.patch('main.create_user', return_value=get_stub_output_user)
    response = get_client.post('/reg', json=get_stub_user.dict())
    assert response.status_code == 200
    assert response.json().get('email') == get_stub_output_user.email
    assert response.json().get('first_name') == get_stub_output_user.first_name
    assert response.json().get('last_name') == get_stub_output_user.last_name
