async def test_reg(mocker, get_stub_output_user, get_client, get_stub_user):
    mocker.patch('main.create_user', return_value=get_stub_output_user)
    response = get_client.post('/reg', json=get_stub_user.dict())
    assert response.status_code == 200
    assert response.json().get('email') == get_stub_output_user.email
    assert response.json().get('first_name') == get_stub_output_user.first_name
    assert response.json().get('last_name') == get_stub_output_user.last_name


async def test_auth(mocker, get_stub_authenticate, get_stub_create_token, get_client, get_stub_form):
    mocker.patch('main.authenticate', return_value=get_stub_authenticate)
    mocker.patch('main.create_token', return_value=get_stub_create_token)
    form_data = get_stub_form
    response = get_client.post('/login/token', data=form_data)
    assert response.status_code == 200
    assert response.json().get('access_token') == get_stub_create_token
    assert response.json().get('token_type') == 'bearer'


async def test_auth_failed_miss_pass(get_client, get_stub_form_invalid):
    form_data = get_stub_form_invalid
    response = get_client.post('/login/token', data=form_data)
    assert response.status_code == 422
    assert response.json().get('detail')[0].get('msg') == 'field required'
