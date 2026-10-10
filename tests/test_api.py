from fastapi.testclient import TestClient

from src.api.app import app


client = TestClient(app)


def test_health_route():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_sample_pipeline_route():
    response = client.post('/pipeline/run', json={'source': 'sample', 'use_pretrained': False})
    assert response.status_code == 200
    result = response.json()
    assert result['article_count'] > 0
    assert result['portfolio_asset_count'] == 12
    assert result['scenarios']
    signal = result['signals'][0]
    assert -1.0 <= signal['sentiment'] <= 1.0
    assert signal['event_class']
    assert 1.0 <= signal['impact_score'] <= 10.0
    assert {'before_value', 'after_value', 'loss_value', 'assets'} <= set(result['scenarios'][0])


def test_upload_pipeline_route():
    response = client.post('/pipeline/run', json={
        'source': 'upload',
        'use_pretrained': False,
        'articles': [{
            'title': 'Bank announces debt restructuring after default',
            'summary': 'Credit downgrade and liquidity risks worsen.',
        }],
    })
    assert response.status_code == 200
    result = response.json()
    assert result['article_count'] == 1
    assert result['signals'][0]['event_class'] == 'Credit Event'


def test_stress_route_and_input_bounds():
    result = client.post('/stress-test', json={
        'event_class': 'Credit Event',
        'impact_score': 8.5,
    })
    assert result.status_code == 200
    assert result.json()['triggered'] is True
    assert result.json()['loss_value'] > 0

    invalid = client.post('/stress-test', json={
        'event_class': 'Credit Event',
        'impact_score': 11,
    })
    assert invalid.status_code == 422
