import connexion
import logging
from typing import Dict

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

from openapi_tic_tac_toe.models.game import Game
from openapi_tic_tac_toe.models.games_game_id_put_request import GamesGameIdPutRequest
from openapi_tic_tac_toe.metrics import metrics_make_game_listing
from openapi_tic_tac_toe.metrics import metrics_make_game_created
from openapi_tic_tac_toe.metrics import metrics_make_game_finished
from openapi_tic_tac_toe.metrics import metrics_make_game_get_request
from openapi_tic_tac_toe.metrics import metrics_make_game_delete_request
from openapi_tic_tac_toe.metrics import metrics_make_game_move_request
from openapi_tic_tac_toe.metrics import metrics_games_set_active_total
from openapi_tic_tac_toe.metrics import TicTacToePlayer

from enum import Enum
from typing import Optional
from typing import List

g_logger = logging.getLogger("tictactoe")
g_tracer = trace.get_tracer("tictactoe")

g_games: Dict[int, Game] = {}
g_id = 0

g_active_total = 0
metrics_games_set_active_total(g_active_total)

ERROR_SUCCESS = 200
ERROR_FOUND = ERROR_SUCCESS

ERROR_CREATED = 201

ERROR_DELETED = 204

ERROR_DATA_INVALID = 400
ERROR_MESSAGE_DATA_INVALID = "X or Y position is invalid or this move is already done by human or bot."

ERROR_NOT_FOUND = 404
ERROR_MESSAGE_NOT_FOUND = "Game is not found."

ERROR_ALREADY_DONE = 405
ERROR_MESSAGE_ALREADY_DONE = "Game is already finished with determined state."

class GameFieldUnit(Enum):
    NoOccupied = "NONE"
    HumanOccupied = "HUMAN"
    BotOccupied = "BOT"

class GameState(Enum):
    NoWinnerYet = "CONTINUE"
    HumanWinner = "HUMAN_WIN"
    BotWinner = "BOT_WIN"

DEFAULT_GAME_FIELD_UNIT = GameFieldUnit.NoOccupied
DEFAULT_GAME_FIELD_SIZE = 9
DEFAULT_GAME_FIELD = [DEFAULT_GAME_FIELD_UNIT.value] * DEFAULT_GAME_FIELD_SIZE

DEFAULT_GAME_STATE_UNIT = GameState.NoWinnerYet
DEFAULT_GAME_STATE = DEFAULT_GAME_STATE_UNIT.value

NOT_FOUND = (ERROR_MESSAGE_NOT_FOUND, ERROR_NOT_FOUND)
DATA_INVALID = (ERROR_MESSAGE_DATA_INVALID, ERROR_DATA_INVALID)
ALREADY_DONE = (ERROR_MESSAGE_ALREADY_DONE, ERROR_ALREADY_DONE)

ATT_HTTP_METHOD = "http.request.method"
ATT_HTTP_STATUS = "http.response.status_code"

ATT_GAME_ID = "ttt.game_id"
ATT_GAME_NEW_ID = "ttt.game_created_id"
ATT_GAME_CURR_ACTIVE = "ttt.game_active_total"
ATT_GAME_PREV_ACTIVE = "ttt.game_prev_active_total"
ATT_GAME_TOTAL = "ttt.game_total"
ATT_GAME_LIST = "ttt.game_list"

ATT_GAME_MOVE_PX = "ttt.game_move.px"
ATT_GAME_MOVE_PY = "ttt.game_move.py"
ATT_GAME_MOVE_PLAYER_MOVED = "ttt.game_move.player_moved"
ATT_GAME_MOVE_BOT_MOVED = "ttt.game_move.bot_moved"
ATT_GAME_MOVE_STATUS = "ttt.game_move.status"

ATT_GAME_CHECK_WINNER_EXPECTED = "ttt.game_check_winner.expected"
ATT_GAME_CHECK_WINNER_IS_ROW = "ttt.game_check_winner.is_row"
ATT_GAME_CHECK_WINNER_IS_COLUMN = "ttt.game_check_winner.is_column"
ATT_GAME_CHECK_WINNER_IS_DIAG = "ttt.game_check_winner.is_diag"
ATT_GAME_CHECK_WINNER_ROW = "ttt.game_check_winner.row"
ATT_GAME_CHECK_WINNER_COLUMN = "ttt.game_check_winner.column"
ATT_GAME_CHECK_WINNER_DIAG = "ttt.game_check_winner.diag"
ATT_GAME_CHECK_WINNER_STATUS = "ttt.game_check_winner.status"

def __msg(parent: str, msg: str):
    return f"User called {parent}: {msg}"

def info(parent: str, msg: str):
    g_logger.info(__msg(parent, msg))

def warn(parent: str, msg: str):
    g_logger.warning(__msg(parent, msg))

def add_active_game(parent: str, span: Span):
    global g_active_total

    prev = g_active_total
    g_active_total += 1

    metrics_games_set_active_total(g_active_total)
    info(parent, f"Number of active games increased [prev={prev}, current={g_active_total}]")

    span.set_attribute(ATT_GAME_PREV_ACTIVE, prev)
    span.set_attribute(ATT_GAME_CURR_ACTIVE, g_active_total)

def sub_active_game(parent: str, span: Span):
    global g_active_total

    prev = g_active_total
    g_active_total -= 1

    metrics_games_set_active_total(g_active_total)
    info(parent, f"Number of active games decreased [prev={prev}, current={g_active_total}]")

    span.set_attribute(ATT_GAME_PREV_ACTIVE, prev)
    span.set_attribute(ATT_GAME_CURR_ACTIVE, g_active_total)

def span_name(s: str) -> str:
    return f"ttt_task_games_{'_'.join(s.split(' '))}"

def games_game_id_delete(game_id: int):
    global g_games

    method = "DELETE"
    parent = f"{method} /games/{{game_id}}"

    with g_tracer.start_as_current_span(span_name("delete game")) as span:
        span.set_attribute(ATT_HTTP_METHOD, method)
        span.set_attribute(ATT_GAME_ID, game_id)

        if game_id in g_games:
            g_games.pop(game_id)

            metrics_make_game_delete_request()

            info(parent, f"Game [id={game_id}] successfully deleted")

            sub_active_game(parent, span)

            span.set_attribute(ATT_HTTP_STATUS, ERROR_DELETED)

            return connexion.NoContent, ERROR_DELETED

        metrics_make_game_delete_request(False)

        warn(parent, f"Game [id={game_id}] is not found")

        span.set_attribute(ATT_HTTP_STATUS, ERROR_NOT_FOUND)
        span.set_status(Status(StatusCode.ERROR))

        return NOT_FOUND

def games_game_id_get(game_id: int):
    global g_games

    method = "GET"
    parent = f"{method} /games/{{game_id}}"

    with g_tracer.start_as_current_span(span_name("get game")) as span:
        span.set_attribute(ATT_HTTP_METHOD, method)
        span.set_attribute(ATT_GAME_ID, game_id)

        if game_id in g_games:
            metrics_make_game_get_request()

            info(parent, f"Game [id={game_id}] info retrieved")

            span.set_attribute(ATT_HTTP_STATUS, ERROR_FOUND)

            return g_games[game_id], ERROR_FOUND

        metrics_make_game_get_request(False)

        warn(parent, f"Game [id={game_id}] is not found")

        span.set_attribute(ATT_HTTP_STATUS, ERROR_NOT_FOUND)
        span.set_status(Status(StatusCode.ERROR))

        return NOT_FOUND

def games_game_id_put(game_id: int, body):
    global g_games

    method = "PUT"
    parent = f"{method} /games/{{game_id}}"

    with g_tracer.start_as_current_span(span_name("make move in game")) as span_make_a_move:
        error_p = "undefined"

        span_make_a_move.set_attribute(ATT_HTTP_METHOD, method)
        span_make_a_move.set_attribute(ATT_GAME_ID, game_id)
        span_make_a_move.set_attribute(ATT_GAME_MOVE_PLAYER_MOVED, False)
        span_make_a_move.set_attribute(ATT_GAME_MOVE_BOT_MOVED, False)

        size = 3
        indexes = range(1, size + 1)

        def getpos(x: int, y: int) -> int:
            return (y - 1) * size + (x - 1)

        def check_winner(expected_unit: GameFieldUnit, cells: List[str], who: str) -> bool:
            with g_tracer.start_as_current_span(span_name(f"check is {who} winner")) as span_check_winner:
                expected = expected_unit.value

                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_EXPECTED, expected)
                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_IS_ROW, False)
                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_IS_COLUMN, False)
                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_IS_DIAG, False)
                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_ROW, error_p)
                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_COLUMN, error_p)
                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_DIAG, error_p)
                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_STATUS, True)

                for y in indexes:
                    count = 0

                    for x in indexes:
                        if cells[getpos(x, y)] == expected:
                            count += 1

                    if count == 3:
                        span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_IS_ROW, True)
                        span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_ROW, y)
                        return True

                for x in indexes:
                    count = 0

                    for y in indexes:
                        if cells[getpos(x, y)] == expected:
                            count += 1

                    if count == 3:
                        span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_IS_COLUMN, True)
                        span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_COLUMN, x)
                        return True

                if cells[getpos(1, 1)] == expected and cells[getpos(2, 2)] == expected and cells[getpos(3, 3)] == expected:
                    span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_IS_DIAG, True)
                    span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_DIAG, "left-up-to-right-down")
                    return True

                if cells[getpos(3, 1)] == expected and cells[getpos(2, 2)] == expected and cells[getpos(1, 3)] == expected:
                    span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_IS_DIAG, True)
                    span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_DIAG, "left-down-to-right-up")
                    return True

                span_check_winner.set_attribute(ATT_GAME_CHECK_WINNER_STATUS, False)

                return False

        px: Optional[int] = None
        py: Optional[int] = None

        if not game_id in g_games:
            metrics_make_game_move_request(False)

            warn(parent, f"Game [id={game_id}] is not found")

            span_make_a_move.set_attribute(ATT_HTTP_STATUS, ERROR_NOT_FOUND)
            span_make_a_move.set_attribute(ATT_GAME_MOVE_STATUS, "game not found")
            span_make_a_move.set_status(Status(StatusCode.ERROR))

            return NOT_FOUND

        game = g_games[game_id]

        if GameState(game.game_state) != GameState.NoWinnerYet:
            metrics_make_game_move_request(False)

            warn(parent, f"Game [id={game_id}] can't handle move, because game is already finished")

            span_make_a_move.set_attribute(ATT_HTTP_STATUS, ERROR_DATA_INVALID)
            span_make_a_move.set_attribute(ATT_GAME_MOVE_STATUS, "game is already finished")
            span_make_a_move.set_status(Status(StatusCode.ERROR))

            return ALREADY_DONE

        with g_tracer.start_as_current_span(span_name("check human move")) as span_check_human_move:
            info(parent, f"Game [id={game_id}] handling movement...")

            games_game_id_put_request = body
            if connexion.request.is_json:
                games_game_id_put_request = GamesGameIdPutRequest.from_dict(connexion.request.get_json())
                px = games_game_id_put_request.px
                py = games_game_id_put_request.py

            span_check_human_move.set_attribute(ATT_GAME_MOVE_PX, px if px is not None else error_p)
            span_check_human_move.set_attribute(ATT_GAME_MOVE_PY, py if py is not None else error_p)

            spans = [span_make_a_move, span_check_human_move]
            span_make_a_move_message = f"see {span_name('check human move')} trace"

            if px is None or py is None:
                metrics_make_game_move_request(False)

                warn(parent, f"Game [id={game_id}] can't handle move, because it's invalid")

                for span in spans:
                    span.set_status(Status(StatusCode.ERROR))

                span_make_a_move.set_attribute(ATT_GAME_MOVE_STATUS, span_make_a_move_message)
                span_make_a_move.set_attribute(ATT_HTTP_STATUS, ERROR_DATA_INVALID)

                span_check_human_move.set_attribute(ATT_GAME_MOVE_STATUS, "px or py undefined")

                return DATA_INVALID

            if px < 1 or py < 1 or px > 3 or py > 3:
                metrics_make_game_move_request(False)

                warn(parent, f"Game [id={game_id}] can't handle move, because X/Y is out of range [1, 3]")

                for span in spans:
                    span.set_status(Status(StatusCode.ERROR))

                span_make_a_move.set_attribute(ATT_GAME_MOVE_STATUS, span_make_a_move_message)
                span_make_a_move.set_attribute(ATT_HTTP_STATUS, ERROR_DATA_INVALID)

                span_check_human_move.set_attribute(ATT_GAME_MOVE_STATUS, "px or py out of range")

                return DATA_INVALID

            pos = getpos(px, py)

            if GameFieldUnit(game.game_field[pos]) != GameFieldUnit.NoOccupied:
                metrics_make_game_move_request(False)

                warn(parent, f"Game [id={game_id}] can't handle move, because cell is already occupied")

                for span in spans:
                    span.set_status(Status(StatusCode.ERROR))

                span_make_a_move.set_attribute(ATT_GAME_MOVE_STATUS, span_make_a_move_message)
                span_make_a_move.set_attribute(ATT_HTTP_STATUS, ERROR_DATA_INVALID)

                span_check_human_move.set_attribute(ATT_GAME_MOVE_STATUS, "cell is already occupied")

                return DATA_INVALID

            span_check_human_move.set_attribute(ATT_GAME_MOVE_STATUS, "human's move is checked")

        game.game_field[pos] = GameFieldUnit.HumanOccupied.value

        metrics_make_game_move_request()

        info(parent, f"Game [id={game_id}] player's move is handled")

        span_make_a_move.set_attribute(ATT_GAME_MOVE_PLAYER_MOVED, True)

        if check_winner(GameFieldUnit.HumanOccupied, game.game_field, "human"):
            game.game_state = GameState.HumanWinner.value
            g_games[game_id] = game

            p = TicTacToePlayer.Human
            metrics_make_game_finished(p)

            info(parent, f"Game [id={game_id}] finished with {p.value} winning")

            sub_active_game(parent, span_make_a_move)

            span_make_a_move.set_attribute(ATT_GAME_MOVE_STATUS, "player's winner")
            span_make_a_move.set_attribute(ATT_HTTP_STATUS, ERROR_SUCCESS)

            return game, ERROR_SUCCESS

        bot_moved = False

        for i in range(9):
            if GameFieldUnit(game.game_field[i]) == GameFieldUnit.NoOccupied:
                game.game_field[i] = GameFieldUnit.BotOccupied.value
                bot_moved = True
                break

        info(parent, f"Game [id={game_id}] bot's move is handled")

        span_make_a_move.set_attribute(ATT_GAME_MOVE_BOT_MOVED, bot_moved)

        if check_winner(GameFieldUnit.BotOccupied, game.game_field, "bot"):
            game.game_state = GameState.BotWinner.value
            p = TicTacToePlayer.Bot

            metrics_make_game_finished(p)

            info(parent, f"Game [id={game_id}] finished with {p.value} winning")

            sub_active_game(parent, span_make_a_move)

            span_make_a_move.set_attribute(ATT_GAME_MOVE_STATUS, "bot's winner")
        elif all(GameFieldUnit(cell) != GameFieldUnit.NoOccupied for cell in game.game_field):
            metrics_make_game_finished()

            info(parent, f"Game [id={game_id}] finished with draw")

            sub_active_game(parent, span_make_a_move)

            span_make_a_move.set_attribute(ATT_GAME_MOVE_STATUS, "draw")

        g_games[game_id] = game

        info(parent, f"Game [id={game_id}] handled movement")

        span_make_a_move.set_attribute(ATT_HTTP_STATUS, ERROR_SUCCESS)

        return game, ERROR_SUCCESS

def games_get():
    global g_games

    method = "GET"
    parent = f"{method} /games"

    with g_tracer.start_as_current_span(span_name("listing")) as span:
        span.set_attribute(ATT_HTTP_METHOD, method)
        span.set_attribute(ATT_HTTP_STATUS, ERROR_SUCCESS)

        metrics_make_game_listing()

        span.set_attribute(ATT_GAME_TOTAL, len(g_games))
        l = list(g_games.keys())
        span.set_attribute(ATT_GAME_LIST, l)

        info(parent, f"Games listing returned")

        return l, ERROR_SUCCESS

def games_post():
    global g_games
    global g_id

    method = "POST"
    parent = f"{method} /games"

    with g_tracer.start_as_current_span(span_name("create")) as span:
        span.set_attribute(ATT_HTTP_METHOD, method)
        span.set_attribute(ATT_HTTP_STATUS, ERROR_CREATED)

        g_id += 1
        game = Game(g_id, DEFAULT_GAME_FIELD, DEFAULT_GAME_STATE)
        g_games[g_id] = game

        span.set_attribute(ATT_GAME_NEW_ID, g_id)

        metrics_make_game_created()

        info(parent, f"Game [id={g_id}] was created")

        add_active_game(parent, span)

        return g_id, ERROR_CREATED
