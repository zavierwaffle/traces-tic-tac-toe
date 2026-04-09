import unittest

from flask import json

from openapi_tic_tac_toe.models.game import Game  # noqa: E501
from openapi_tic_tac_toe.models.games_game_id_put_request import GamesGameIdPutRequest  # noqa: E501
from openapi_tic_tac_toe.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_games_game_id_delete(self):
        """Test case for games_game_id_delete

        
        """
        headers = { 
        }
        response = self.client.open(
            '/games/{game_id}'.format(game_id=56),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_games_game_id_get(self):
        """Test case for games_game_id_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/games/{game_id}'.format(game_id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_games_game_id_put(self):
        """Test case for games_game_id_put

        
        """
        games_game_id_put_request = openapi_tic_tac_toe.GamesGameIdPutRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/games/{game_id}'.format(game_id=56),
            method='PUT',
            headers=headers,
            data=json.dumps(games_game_id_put_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_games_get(self):
        """Test case for games_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/games',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_games_post(self):
        """Test case for games_post

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/games',
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
