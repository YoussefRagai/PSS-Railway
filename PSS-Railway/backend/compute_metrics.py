from util_db import get_conn

def compute_player_match_minutes():
    sql = """
    insert into korastats.metrics_player_match (match_id, player_id, team_id, minutes_played, shots, goals, assists)
    select
      l.match_id,
      l.player_id,
      l.team_id,
      90 as minutes_played,
      coalesce(sum((e.event_id in (32,33,34))::int),0) as shots,
      coalesce(sum((e.event_id in (1))::int),0) as goals,
      0 as assists
    from korastats.lineups l
    left join korastats.events e on e.match_id = l.match_id and e.player_id = l.player_id
    group by l.match_id, l.player_id, l.team_id
    on conflict do nothing;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()