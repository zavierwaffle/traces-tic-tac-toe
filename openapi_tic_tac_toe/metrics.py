import prometheus_client

from enum import Enum

from typing import Optional

class TicTacToePlayer(Enum):
    Human = "human",
    Bot = "bot"

ttt_http_request_total_counter = prometheus_client.Counter(
    name = "ttt_http_requests_total",
    documentation = "Total number of HTTP requests handled by the app.",
    labelnames = ["method", "endpoint", "status_code"],
)

ttt_game_listing_requests = prometheus_client.Counter(
    name = "ttt_games_list_total",
    documentation = "Total number of game listing requests."
)

ttt_created_games = prometheus_client.Counter(
    name = "ttt_games_created_total",
    documentation = "Total number of created games.",
)

ttt_game_get_success_requests = prometheus_client.Counter(
    name = "ttt_game_get_request_success_total",
    documentation = "Total number of success game get requests."
)

ttt_game_get_failed_requests = prometheus_client.Counter(
    name = "ttt_game_get_request_failed_total",
    documentation = "Total number of failed game get requests."
)

ttt_game_delete_success_requests = prometheus_client.Counter(
    name = "ttt_game_delete_request_success_total",
    documentation = "Total number of successfully game delete requests.",
)

ttt_game_delete_failed_requests = prometheus_client.Counter(
    name = "ttt_game_delete_request_failed_total",
    documentation = "Total number of failed game delete requests.",
)

ttt_game_move_success_requests = prometheus_client.Counter(
    name = "ttt_game_move_request_success_total",
    documentation = "Total number of player's game movement success attempt.",
)

ttt_game_move_failed_requests = prometheus_client.Counter(
    name = "ttt_game_move_request_failed_total",
    documentation = "Total number of player's game movement failed attempt.",
)

ttt_finished_games = prometheus_client.Counter(
    name = "ttt_completed_games_total",
    documentation = "Total number of completed games.",
)

ttt_player_wins = prometheus_client.Counter(
    name = "ttt_player_win_total",
    documentation = "Total number of completed games, where Player is winner.",
)

ttt_bot_wins = prometheus_client.Counter(
    name = "ttt_bot_win_total",
    documentation = "Total number of completed games, where Bot is winner.",
)

ttt_nobody_wins = prometheus_client.Counter(
    name = "ttt_nobody_win_total",
    documentation = "Total number of completed draw games.",
)

ttt_active_games = prometheus_client.Gauge(
    name = "ttt_active_games",
    documentation = "Number of games currently stored in memory.",
)

def metrics_observe_http_request(method: str, endpoint: str, status_code: int, duration_seconds: float):
    status = str(status_code)
    ttt_http_request_total_counter.labels(method = method, endpoint = endpoint, status_code = status).inc()

def metrics_get_payload() -> bytes:
    return prometheus_client.generate_latest()

def metrics_make_game_listing():
    ttt_game_listing_requests.inc()

def metrics_make_game_created():
    ttt_created_games.inc()

def metrics_make_game_finished(winner: Optional[TicTacToePlayer] = None):
    ttt_finished_games.inc()

    if winner == TicTacToePlayer.Human:
        ttt_player_wins.inc()
    elif winner == TicTacToePlayer.Bot:
        ttt_bot_wins.inc()
    else:
        ttt_nobody_wins.inc()

def metrics_make_game_get_request(success: bool = True):
    if success:
        ttt_game_get_success_requests.inc()
    else:
        ttt_game_get_failed_requests.inc()

def metrics_make_game_delete_request(success: bool = True):
    if success:
        ttt_game_delete_success_requests.inc()
    else:
        ttt_game_delete_failed_requests.inc()

def metrics_make_game_move_request(success: bool = True):
    if success:
        ttt_game_move_success_requests.inc()
    else:
        ttt_game_move_failed_requests.inc()

def metrics_games_set_active_total(total: int):
    ttt_active_games.set(total)
