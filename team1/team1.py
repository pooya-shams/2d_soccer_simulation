import math
import random
from math import sin, cos, radians, sqrt, atan2, degrees
from runner.settings import FRICTION, SCREEN_WIDTH as SW, SCREEN_HEIGHT as SH
from runner.settings import BALL_RADIUS, ALLOWED_PLAYERS_AROUND_BALL_RADIUS


class going_near_ball:
    value = False


class has_moved:
    value = [False] * 6


def out_of_screen(point):
    x = point['x']
    y = point['y']
    if -SW // 2 < x < SW // 2 and -SH // 2 < y < SH // 2:
        return False
    return True


def near_ball(player, ball):
    if get_distance(player, ball) <= ALLOWED_PLAYERS_AROUND_BALL_RADIUS:
        return True
    return False


def players_near_ball(players, player_number, point2, ball, not_owner=False):
    for player in players:
        if player["number"] == player_number:
            continue
        if ball["owner_color"] == "red" and\
                ball["owner_number"] == player_number and\
                not_owner:
            continue
        if near_ball(player, point2):
            return player["number"]
    return None


def players_are_near_ball(players, player_number, point2, ball, not_owner=False):
    if players_near_ball(players, player_number, point2, ball, not_owner) is None:
        return False
    return True


def find_other_head_of_triangle(p2, ball):
    x1 = p2['x']
    y1 = p2['y']
    x2 = ball['x']
    y2 = ball['y']
    dis = get_distance(p2, ball)
    dis2 = dis / 2
    xm = (x1 + x2) / 2
    ym = (y1 + y2) / 2
    h_length2 = (ALLOWED_PLAYERS_AROUND_BALL_RADIUS ** 2) - (dis2 ** 2)
    if h_length2 < 0:
        return None
    h = sqrt(h_length2)
    alpha = degrees(atan2(y2 - y1, x2 - x1)) % 360
    beta = 90 - alpha
    dx = h * cos(radians(beta))
    dy = h * cos(radians(beta))
    nx1 = xm + dx
    ny1 = ym - dy
    nx2 = xm - dx
    ny2 = ym + dy
    return {'x': nx1, 'y': ny1}, {'x': nx2, 'y': ny2}


def find_best_head_of_triangle(p1, p2, ball):
    heads = find_other_head_of_triangle(p1, ball)
    if heads is None:
        return None
    point1 = heads[0]
    point2 = heads[1]
    if out_of_screen(point1):
        return point2
    elif out_of_screen(point2):
        return point1
    else:
        return max((point1, point2), key=lambda x: get_distance(x, p2))


def move(decisions, player_number, destination, speed):
    decisions.append({
        'action': 'move',
        'player_number': player_number,
        'destination': destination,
        'speed': speed,
    })


def kick(decisions, player_number, direction, power):
    decisions.append({
        'action': 'kick',
        'player_number': player_number,
        'direction': clock_to_degree(direction),
        'power': power,
    })


def grab(decisions, player_number):
    decisions.append({
        'action': 'grab',
        'player_number': player_number
    })


def degree_to_clock(degree):
    if degree < 90:
        degree += 360
    degree = 450 - degree
    hour = degree // 30
    minute = degree % 30 // 6
    return hour + minute / 10


def clock_to_degree(clock):
    angle = int(clock // 1 * 30 + 10 * (clock % 1) * 6)
    angle = 450 - angle
    if angle >= 360:
        angle -= 360
    return angle


def get_direction(a, b):
    x = b['x'] - a['x']
    y = b['y'] - a['y']
    angle = math.degrees(math.atan2(y, x))
    return degree_to_clock(angle)


def get_distance(a, b):
    return math.hypot(a['x'] - b['x'], a['y'] - b['y'])


def pg_on_line(ap, bp, cp, er=5):
    x1, y1 = ap["x"], ap["y"]
    x2, y2 = bp["x"], bp["y"]
    x3, y3 = cp["x"], cp["y"]
    bx, kx = max(x1, x2), min(x1, x2)
    by, ky = max(y1, y2), min(y1, y2)
    if kx <= x3 <= bx and ky <= y3 <= by:
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0:
            if abs(x1-x3) < er:
                return True
            return False
        elif dy == 0:
            if abs(y1-y3) < er:
                return True
            return False
        else:
            m = dy / dx
        b = y1 - m * x1
        y = m*x3+b
        if abs(y-y3) < er:
            return True
    return False


def non_of_enemies_on_line(ap, bp, enemies, er=None):
    for i in enemies:
        if er is None:  # means that we should find the error ourselves
            er = 5
            if i["number"] == 0:
                er = 7.5
            er += 4
        if pg_on_line(ap, bp, i, er):
            return False
    return True


def any_enemies_near(p, enemies, radius=18):
    for i in range(6):
        if get_distance(enemies[i], p) <= radius:
            return True
    return False


def sort_by_distance(players, i, not_lis):
    lis = []
    for j in range(6):
        if j != i and (j not in not_lis):
            lis.append({"n": j,
                        "d": get_distance(players[i], players[j])})
    lis = list(sorted(lis, key=lambda x: x["d"]))
    lis = list(map(lambda x: x["n"], lis))
    return lis[:]


def search_for_good_teammate(players, enemies, i, ball, not_lis, con2=True) -> (int):
    sorted_players = sort_by_distance(players, i, not_lis)
    for j in sorted_players:
        if non_of_enemies_on_line(players[i], players[j], enemies):
            if not con2:
                return j
            else:
                if not any_enemies_near(players[i], enemies, 22):
                    return j
    if con2:
        return search_for_good_teammate(players, enemies, i, ball,
                                        not_lis=not_lis, con2=False)
    return sorted_players[0]


def search_for_forward_teammate(players, enemies, i, ball, not_lis):
    # list of indexes
    lis = []
    n = 0
    for j in range(6):
        if i != j and j not in not_lis:
            x1 = players[i]['x']
            x2 = players[j]['x']
            if x2 >= x1 and x2-x1 <= 60:
                lis.append(j)
                n += 1
    if n == 0:
        return None
    return lis[random.randint(0, n-1)]


def min_index(lis):
    m = lis[0]
    mi = 0
    for i in range(1, len(lis)):
        mm = lis[i]
        if mm < m:
            mi = i
            mm = m
    return mi


def ball_next(ball, players, enemies):
    ball = ball.copy()
    players = players.copy()
    enemies = enemies.copy()
    red = "red"
    blue = "blue"
    white = "white"
    direction = clock_to_degree(ball["direction"])
    speed = ball["speed"]
    color = ball["owner_color"]
    radius = BALL_RADIUS
    number = ball["owner_number"]
    x = ball['x']
    y = ball['y']
    if color is white:
        x += speed * cos(radians(direction))
        y += speed * sin(radians(direction))
        speed -= FRICTION
        if speed < 0:
            speed = 0
        if x < -SW // 2 + radius:
            x = -SW // 2 + radius + 1
            direction = 180 - direction
        if x > SW // 2 - radius:
            x = SW // 2 - radius - 1
            direction = 180 - direction
        if y < -SH // 2 + radius:
            y = -SH // 2 + radius + 1
            direction = (direction + 180) % 360
            direction = 180 - direction
        if y > SH // 2 - radius:
            y = SH // 2 - radius - 1
            direction = (direction + 180) % 360
            direction = 180 - direction

    else:
        teams = {red: players, blue: enemies}
        x = teams[color][number]['x']
        y = teams[color][number]['y']

    ball['x'] = x
    ball['y'] = y
    ball["speed"] = speed
    ball["direction"] = degree_to_clock(direction)
    return ball


def predict_ball(ball, players, enemies, iterations=1):
    b = ball.copy()
    p = players.copy()
    e = enemies.copy()
    for _ in range(iterations):
        b = ball_next(b, p, e)
    return b


def play(red_players, blue_players, red_score, blue_score, ball, time_passed):
    decisions = []
    ###########################################################################
    red = "red"
    blue = "blue"
    white = "white"
    players = red_players
    enemies = blue_players
    enemie_goal_mean = {'x': 484, 'y': 0}
    enemie_goal_min = {'x': 484, 'y': -80}
    enemie_goal_max = {'x': 484, 'y': 80}
    ball_color = ball["owner_color"]
    ball_number = ball["owner_number"]
    ball_x = ball['x']
    ball_y = ball['y']
    player_radiuses = [7.5, 5, 5, 5, 5, 5]
    ball_radius = BALL_RADIUS
    ball_speed = ball["speed"]
    ball_dir = ball["direction"]
    go_poses = [{'x': -436, 'y': 0},
                {'x': -450, 'y': -60},
                {'x': -450, 'y': 60},
                enemie_goal_mean,
                enemie_goal_max,
                enemie_goal_min]
    distances_for_players = [23]+([18]*5)
    near_distance = sqrt((92.5 ** 2) * 2)
    distance_from_goal = 170
    distance_for_defence_x_s = [-300, -300, -300]
    distance_for_defence_y_abs = 162.5
    # movement_error = 30
    max_speed = 10
    max_power = 60
    # er = 10
    going_near_ball.value = False
    # will be set to True when a move will make a player to go near ball
    # this will warn future players not to go near the ball!
    # pretty genious! ha?
    has_moved.value = [False] * 6
    attacker_moving_to_ball = None

    def do_move(decisions, i, destination, speed=max_speed):
        # if has_moved.value[i]:
        #     return
        speed = min(speed, max_speed)
        player = players[i]
        distance = get_distance(player, destination)
        if distance == 0:
            return
        if player["ban_cycles"] != 0:
            return
        x = 0
        y = 0
        if distance < speed:
            x = destination['x']
            y = destination['y']
        else:
            ratio = speed / distance
            dx = destination['x'] - player['x']
            dy = destination['y'] - player['y']
            x = player['x'] + ratio * dx
            y = player['y'] + ratio * dy
        new_destination = {'x': x, 'y': y}
        players_near_player_detected_not_owner = players_near_ball(
            players, i, player, ball, not_owner=True)
        players_near_player_detected = players_near_ball(
            players, i, player, ball)
        if players_near_player_detected is not None:
            # checking if there are any players near
            # the player that may be banned after
            # a kick near them
            near_player = players[players_near_player_detected]
            if ball_color == red and \
                    ball_number == near_player["number"] and \
                    players_near_player_detected_not_owner is not None:
                near_player = players[players_near_player_detected_not_owner]
            pos = find_best_head_of_triangle(player, near_player, player)
            if pos is not None:
                move(decisions, i, pos, min(get_distance(player, pos), max_speed))
                has_moved.value[i] = True
                return
        if near_ball(new_destination, ball):
            if players_are_near_ball(players, i, ball, ball) or \
                    going_near_ball.value:
                return
            going_near_ball.value = True
        move(decisions, i, destination, speed)
        has_moved.value[i] = True

    def move_to_ball(decisions, i):
        if not players_are_near_ball(players, i, ball, ball):
            speed = get_distance(players[i], ball)
            do_move(decisions, i, ball, speed)

    # firts do the defend (players 0 ~ 2)
    for i in range(3):
        p = players[i]
        b = ball.copy()
        if ball_speed > 0 and ball_color != red:  # the ball is comming!
            if ball_dir >= 6.0:
                b['x'] = go_poses[i]['x']
        tmpb = b
        lb = b
        for j in range(1, 4):
            # if the ball will be goaled in j cycles away, we'll go to cycle j-1
            nb = ball_next(lb, players, enemies)
            if nb['x'] <= -SW // 2 + ball_radius + 1:
                tmpb = lb
            lb = nb
        b = tmpb
        # if tmpd > movement_error:
        #    b['y'] = go_poses[i]['y'] + copysign(movement_error, b['y']-go_poses[i]['y'])
        # no need to them anymore, the players won't get near to eachother
        for j in range(3):
            if i != j:
                p2 = players[j]
                dis = b['y'] - p2['y']
                min_dis = (player_radiuses[i] + player_radiuses[j])
                if 0 <= dis < min_dis:  # the players will hit
                    # avoid the current player from going that near
                    b['y'] = p2['y'] + \
                        (player_radiuses[i] + player_radiuses[j])
        dpb = get_distance(players[i], ball)
        # near = False
        # if get_distance(ball, players[i]) < near_distance:
        #     near = True
        # for j in range(3):
        #    if get_distance(ball, players[j]) < get_distance(ball, players[i]):
        #        near = False
        if ball_x <= distance_for_defence_x_s[i]:  # and near:
            if -distance_for_defence_y_abs <= ball_y <= distance_for_defence_y_abs:
                if ball_color == red and ball_number == i:
                    j = search_for_good_teammate(
                        players, enemies, i, ball, [0, 1, 2])
                    kick(decisions, i, get_direction(
                        p, players[j]), max_power)
                elif dpb < distances_for_players[i]:
                    if ball_color != red:
                        grab(decisions, i)
                        j = search_for_good_teammate(
                            players, enemies, i, ball, [0, 1, 2])
                        kick(decisions, i, get_direction(
                            p, players[j]), max_power)
                elif dpb < distances_for_players[i] + max_speed:
                    move_to_ball(decisions, i)
                    grab(decisions, i)
                    j = search_for_good_teammate(
                        players, enemies, i, ball, [0, 1, 2])
                    kick(decisions, i, get_direction(
                        p, players[j]), max_power)
                else:
                    do_move(decisions, i, b, get_distance(p, b))
                    grab(decisions, i)
                    j = search_for_good_teammate(
                        players, enemies, i, ball, [0, 1, 2])
                    kick(decisions, i, get_direction(
                        p, players[j]), max_power)
            elif distances_for_players[i] < dpb + max_speed:
                do_move(decisions, i, b)
                grab(decisions, i)
                j = search_for_good_teammate(
                    players, enemies, i, ball, [0, 1, 2])
                kick(decisions, i, get_direction(
                    p, players[j]), max_power)
            else:
                do_move(decisions, i, go_poses[i])
        else:
            do_move(decisions, i, go_poses[i])
    # now lets attask!
    # but waht should we do?
    # go near the goal and goal a goal?
    # do this by passing the ball?
    # attack (players 4 ~ 5)
    for i in range(4, 6):
        p = players[i]
        px, py = p['x'], p['y']
        if ball_color != red:  # we don't have the ball
            # we can grab the ball
            if get_distance(p, ball) < distances_for_players[i]:
                if ball_color == blue:  # the ball is grabbed by enemies
                    grab(decisions, i)
                # the ball is opposite us or makes no changes
                # so we should grab it
                elif ball_color == white:
                    if ball_speed == 0:
                        # the ball is stopped so we had better grab it
                        grab(decisions, i)
                    # the ball is comming through us! we should stop it
                    # so we can attack later!
                    elif 0.0 <= ball_dir <= 6.0:
                        grab(decisions, i)
            else:
                # we can not grab the ball so we will move through it
                if ball_x < 0 and px > 0 and ball_color != red:
                    # we are being attacked! go back to defence!
                    move_to_ball(decisions, i)
                elif attacker_moving_to_ball is None:
                    attacker_moving_to_ball = i
                else:
                    # there is someone else going for the ball
                    attacker = players[attacker_moving_to_ball]
                    dis_attacker = get_distance(ball, attacker)
                    dis_us = get_distance(p, ball)
                    if dis_us < dis_attacker or attacker["ban_cycles"] != 0:
                        do_move(decisions,
                                attacker_moving_to_ball,
                                go_poses[attacker_moving_to_ball])
                        attacker_moving_to_ball = i

        # elif ball_number not in [3, 4, 5]:
        # # the ball is grabbed by the defenders
        #    move(decisions, i, ball, min(get_distance(p, ball), max_speed))
        #    kick(decisions, ball_number, get_direction(
        #        players[ball_number], enemie_goal_mean), max_power)
        elif ball_number != i:  # the ball is grabbed by attacker but not us
            players_near_ball_detected = players_near_ball(
                players, i, ball, ball)
            if players_near_ball_detected is None:
                do_move(decisions, i, go_poses[i])
            else:
                near_player = players[players_near_ball_detected]
                pos = find_best_head_of_triangle(p, near_player, ball)
                if pos is not None:
                    do_move(decisions, i, pos, get_distance(p, pos))
        else:  # the ball is grabbed by us (attackers)
            dmean = get_distance(p, enemie_goal_mean)
            dmin = get_distance(p, enemie_goal_min)
            dmax = get_distance(p, enemie_goal_max)
            # its better to attack through which part of the goal
            if dmean <= distance_from_goal and \
                    non_of_enemies_on_line(p, enemie_goal_mean, enemies):
                kick(decisions, i, get_direction(
                    p, enemie_goal_mean), max_power)
            elif dmin <= distance_from_goal and \
                    non_of_enemies_on_line(p, enemie_goal_min, enemies):
                kick(decisions, i, get_direction(
                    p, enemie_goal_min), max_power)
            elif dmax <= distance_from_goal and \
                    non_of_enemies_on_line(p, enemie_goal_max, enemies):
                kick(decisions, i, get_direction(
                    p, enemie_goal_max), max_power)
            # non of them are good to go through so we will pass the ball or...
            # we shouldn't let the enemies grab the ball!
            elif any_enemies_near(ball, enemies):
                j = search_for_good_teammate(
                    players, enemies, i, ball, not_lis=[0, 1, 2])
                pj = players[j]
                distance = get_distance(p, pj)
                direction = get_direction(p, pj)
                kick(decisions, i, direction, min(distance, max_power))
            else:
                k = search_for_forward_teammate(
                    players, enemies, i, ball, not_lis=[0, 1, 2])
                if k is not None:
                    pk = players[k]
                    if non_of_enemies_on_line(p, pk, enemies):
                        distance = get_distance(p, pk)
                        direction = get_direction(p, pk)
                        kick(decisions, i, direction, min(distance, max_power))
                        continue
                j = search_for_good_teammate(
                    players, enemies, i, ball, not_lis=[0, 1, 2])
                pj = players[j]
                if pj['x'] <= px:
                    pos = go_poses[i]
                    lis = [dmean, dmin, dmax]
                    index = min_index(lis)+3
                    npos = go_poses[index]
                    if non_of_enemies_on_line(p, npos, enemies):
                        do_move(decisions, i, npos)
                    elif non_of_enemies_on_line(p, pos, enemies):
                        # pass the ball
                        do_move(decisions, i, pos)
                    else:
                        pos = go_poses[j]
                        djmean = get_distance(pj, enemie_goal_mean)
                        djmin = get_distance(pj, enemie_goal_min)
                        djmax = get_distance(pj, enemie_goal_max)
                        lj = [djmean, djmin, djmax]
                        jind = min_index(lj)+3
                        npos = go_poses[jind]
                        if non_of_enemies_on_line(pj, npos, enemies):
                            d = get_distance(p, pj)
                            kick(decisions, i, get_direction(
                                p, pj), min(d, max_power))
                            grab(decisions, j)
                            do_move(decisions, j, npos)
                        elif non_of_enemies_on_line(pj, pos, enemies):
                            d = get_distance(p, pj)
                            kick(decisions, i, get_direction(
                                p, pj), min(d, max_power))
                            grab(decisions, j)
                            do_move(decisions, j, pos)
                        else:
                            yy = 0
                            if py == yy:
                                yy = py + random.randint(-18, 18)
                            des = {'x': px, 'y': yy}
                            do_move(decisions, i, des)
                else:  # pass the ball
                    d = get_distance(p, pj)
                    kick(decisions, i, get_direction(p, pj), min(d, max_power))

    for i in [3]:  # just using a loop to seperate from other stuff
        p = players[i]
        if ball_color == red:  # we have the ball
            poses = [enemie_goal_min, enemie_goal_max]
            pos = poses[random.randint(0, 1)]
            if ball_number == i:
                if get_distance(p, pos) > distance_from_goal:  # we can't kick the ball
                    if non_of_enemies_on_line(p, pos, enemies) and \
                            not any_enemies_near(p, enemies):
                        do_move(decisions, i, pos)
                    else:
                        k = search_for_forward_teammate(
                            players, enemies, i, ball, [0, 1, 2])
                        if k is not None:
                            pk = players[k]
                            if non_of_enemies_on_line(p, pk, enemies):
                                distance = get_distance(p, pk)
                                direction = get_direction(p, pk)
                                kick(decisions, i, direction,
                                     min(distance, max_power))
                                continue
                        do_move(decisions, i, pos)
                else:  # we can kick the ball (to where?)
                    kick(decisions, i, get_direction(p, pos), max_power)
                continue
        # do_move(decisions, i, ball)
        if ball_x < 0 and px > 0 and ball_color != red:
            # we are being attacked! go back to defence!
            move_to_ball(decisions, i)
        elif attacker_moving_to_ball is None:
            attacker_moving_to_ball = i
        else:
            attacker = players[attacker_moving_to_ball]
            dis_attacker = get_distance(ball, attacker)
            dis_us = get_distance(p, ball)
            if dis_us < dis_attacker or attacker["ban_cycles"] != 0:
                do_move(decisions,
                        attacker_moving_to_ball,
                        go_poses[attacker_moving_to_ball])
                attacker_moving_to_ball = i
        grab(decisions, i)

    # moving the chosen attacker to the ball
    if attacker_moving_to_ball is not None:
        if ball_color == red:
            i = attacker_moving_to_ball
            des = go_poses[i]
            attacker = players[i]
            do_move(decisions, i, des, get_distance(attacker, des))
        else:
            attacker = players[attacker_moving_to_ball]
            move_to_ball(decisions, attacker_moving_to_ball)

    for i in range(0, 6):
        if not has_moved.value[i]:
            p = players[i]
            pos = go_poses[i]
            do_move(decisions, i, pos, get_distance(p, pos))
    ###########################################################################
    return decisions
