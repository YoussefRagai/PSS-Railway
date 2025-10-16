import os, time, requests
from typing import Any, Dict, List
from util_db import get_conn, upsert_many

API_BASE = "https://korastats.pro/pro/api.php"
API_VERSION = "V2"
LANG = "en"
API_KEY = os.getenv("KORASTATS_API_KEY")
if not API_KEY:
    raise SystemExit("❌ Set KORASTATS_API_KEY env var.")

def ks_get(api: str, params: Dict[str, Any]) -> Dict[str, Any]:
    q = {
        "module": "api", "api": api, "version": API_VERSION,
        "response": "json", "lang": LANG, "key": API_KEY, **params
    }
    r = requests.get(API_BASE, params=q, timeout=60)
    r.raise_for_status()
    return r.json()

def g(o, *ks, default=None):
    cur = o
    for k in ks:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

# ---------- Fetchers ----------
def fetch_seasons() -> List[dict]:
    out, page = [], 1
    while True:
        res = ks_get("SeasonList", {"page_number": page, "page_size": 100})
        data = g(res, "root","object","Data", default=[])
        if not data: break
        out += data
        pages = g(res, "root","object","pages", default=1) or g(res,"root","object","PageCount", default=1)
        if page >= pages: break
        page += 1; time.sleep(0.15)
    return out

def fetch_matches(season_id: int) -> List[dict]:
    out, page = [], 1
    while True:
        res = ks_get("SeasonMatchList", {"season_id": season_id, "page_number": page, "page_size": 100})
        data = g(res,"root","object","Data", default=[])
        if not data: break
        out += data
        pages = g(res,"root","object","PageCount", default=page)
        if page >= (pages or page): break
        page += 1; time.sleep(0.15)
    return out

def fetch_match_full(match_id: int) -> dict:
    res = ks_get("MatchEventList", {"match_id": match_id})
    return res.get("data") or {}

# ---------- Stagers ----------
def stage_competitions(seasons: List[dict]):
    countries, organizers, ages, tournaments, seasons_rows = [], [], [], [], []
    seen_c, seen_o, seen_a, seen_t = set(), set(), set(), set()
    for s in seasons:
        t = s.get("tournament", {}) or {}
        org = t.get("organizer", {}) or {}
        ctry = org.get("country", {}) or {}
        age = t.get("age_group", {}) or {}
        if (cid := ctry.get("id")) and cid not in seen_c:
            countries.append({"id": cid, "name": ctry.get("name")}); seen_c.add(cid)
        if (oid := org.get("id")) and oid not in seen_o:
            organizers.append({"id": oid, "name": org.get("name"), "country_id": cid}); seen_o.add(oid)
        if (aid := age.get("id")) and aid not in seen_a:
            ages.append({"id": aid, "name": age.get("name")}); seen_a.add(aid)
        if (tid := t.get("id")) and tid not in seen_t:
            tournaments.append({"id": tid, "name": t.get("name"), "gender": t.get("gender"),
                                "organizer_id": oid, "age_group_id": aid}); seen_t.add(tid)
        seasons_rows.append({"id": s.get("id"), "name": s.get("name"), "gender": s.get("gender"),
                             "nature": s.get("nature"), "tournament_id": tid,
                             "start_date": s.get("startDate"), "end_date": s.get("endDate")})
    return countries, organizers, ages, tournaments, seasons_rows

def stage_matches(ms: List[dict]):
    teams, stadiums, referees, assistants, matches_rows = [], [], [], [], []
    seen_team, seen_st, seen_ref, seen_ast = set(), set(), set(), set()
    for m in ms:
        mid = m.get("matchId")
        for side in ("home","away"):
            t = m.get(side) or {}
            if t.get("id") and t["id"] not in seen_team:
                teams.append({"id": t["id"], "name": t.get("name")}); seen_team.add(t["id"])
        st = m.get("stadium") or {}
        if st.get("id") and st["id"] not in seen_st:
            stadiums.append({"id": st["id"], "name": st.get("name")}); seen_st.add(st["id"])
        ref = m.get("referee") or {}
        if ref.get("id") and ref["id"] not in seen_ref:
            referees.append({"id": ref["id"], "name": ref.get("name"),
                             "dob": ref.get("dob"), "nationality_id": g(ref,"nationality","id")})
            seen_ref.add(ref["id"])
        for ak in ("assistant1","assistant2"):
            a = m.get(ak) or {}
            if a.get("id") and a["id"] not in seen_ast:
                assistants.append({"id": a["id"], "name": a.get("name"),
                                   "dob": a.get("dob"), "gender": a.get("gender"),
                                   "nationality_id": g(a,"nationality","id")})
                seen_ast.add(a["id"])
        matches_rows.append({
            "id": mid,
            "tournament_id": g(m,"tournament","id"),
            "season_id": g(m,"season","id"),
            "round": m.get("round"),
            "stadium_id": g(m,"stadium","id"),
            "date_time": m.get("dateTime"),
            "last_update": m.get("dtLastUpdateDateTime"),
            "score_home": g(m,"score","home"),
            "score_away": g(m,"score","away"),
            "status_id": g(m,"status","id"),
            "status_name": g(m,"status","name")
        })
    return teams, stadiums, referees, assistants, matches_rows

def stage_match_full(match_id: int, d: dict):
    teams, players, lineups = [], [], []
    events, cats, types, results, bparts = [], [], [], [], []
    seen_team, seen_player, seen_c, seen_t, seen_r, seen_b = set(), set(), set(), set(), set(), set()

    for side in ("home","away"):
        t = d.get("match",{}).get(side, {}) or {}
        tid = t.get("id"); 
        if tid and tid not in seen_team:
            teams.append({"id": tid, "name": t.get("name"), "logo": t.get("logo")}); seen_team.add(tid)
        for group, role in (("lineup","starter"),("sub","sub")):
            for p in (t.get(group, {}) or {}).values():
                pid = p.get("id")
                if pid and pid not in seen_player:
                    players.append({
                        "id": pid, "name": p.get("name"), "nickname": p.get("nickname"),
                        "dob": p.get("dob"), "primary_position_id": p.get("primary_position_id"),
                        "primary_position_name": p.get("primary_position_name"),
                        "secondary_position_id": p.get("secondary_position_id"),
                        "secondary_position_name": p.get("secondary_position_name")
                    }); seen_player.add(pid)
                lineups.append({
                    "match_id": match_id, "team_id": tid, "player_id": pid,
                    "shirt_number": p.get("shirt_number"), "role": role, "side": side
                })

    evs = d.get("events") or d.get("match",{}).get("events",[]) or []
    for ev in evs:
        if (cid:=ev.get("category_id")) and cid not in seen_c:
            cats.append({"id": cid, "name": ev.get("category")}); seen_c.add(cid)
        if (eid:=ev.get("event_id")) and eid not in seen_t:
            types.append({"id": eid, "name": ev.get("event")}); seen_t.add(eid)
        if (rid:=ev.get("result_id")) and rid not in seen_r:
            results.append({"id": rid, "name": ev.get("result")}); seen_r.add(rid)
        if (bid:=ev.get("body_part_id")) and bid not in seen_b:
            bparts.append({"id": bid, "name": ev.get("body_part")}); seen_b.add(bid)
        events.append({
            "match_id": match_id, "team_id": ev.get("team_id"), "player_id": ev.get("player_id"),
            "nickname": ev.get("nickname"), "shirt_number": ev.get("shirt_number"),
            "half": ev.get("half"), "minute": ev.get("min") or ev.get("minute"),
            "second": ev.get("sec"), "msec": ev.get("msec"), "time_in_sec": ev.get("timeInSec"),
            "x": ev.get("x"), "y": ev.get("y"),
            "category_id": cid, "event_id": eid, "result_id": rid,
            "guid": ev.get("guid"), "guid_ref": ev.get("guid_ref"),
            "extra": ev.get("extra"), "extra_id": ev.get("extra_id"),
            "body_part_id": bid
        })
    return teams, players, lineups, cats, types, results, bparts, events

# ---------- Pipeline ----------
def run_etl(limit_seasons: int | None = None, limit_matches: int | None = None):
    seasons = fetch_seasons()
    if limit_seasons: seasons = seasons[:limit_seasons]

    with get_conn() as conn:
        countries, organizers, ages, tournaments, seasons_rows = stage_competitions(seasons)
        upsert_many(conn, "countries", countries)
        upsert_many(conn, "organizers", organizers)
        upsert_many(conn, "age_groups", ages)
        upsert_many(conn, "tournaments", tournaments)
        upsert_many(conn, "seasons", seasons_rows)
        conn.commit()

        for s in seasons_rows:
            ms = fetch_matches(s["id"])
            if limit_matches: ms = ms[:limit_matches]
            teams, stadiums, refs, assts, matches_rows = stage_matches(ms)

            # heal nationality FKs for officials
            missing_country_ids = {r["nationality_id"] for r in refs+assts if r.get("nationality_id")} - {c["id"] for c in countries}
            for cid in sorted(missing_country_ids):
                # if API has no country endpoint, insert placeholder
                upsert_many(conn, "countries", [{"id": cid, "name": f"Country {cid}"}])
            upsert_many(conn, "teams", teams)
            upsert_many(conn, "stadiums", stadiums)
            upsert_many(conn, "referees", refs)
            upsert_many(conn, "assistants", assts)
            upsert_many(conn, "matches", matches_rows)
            conn.commit()

            for m in matches_rows:
                full = fetch_match_full(m["id"])
                t2, players, lineups, cats, types, results, bparts, events = stage_match_full(m["id"], full)

                upsert_many(conn, "teams", t2)  # adds logos
                upsert_many(conn, "players", players)
                upsert_many(conn, "lineups", lineups)
                upsert_many(conn, "event_categories", cats)
                upsert_many(conn, "event_types", types)
                upsert_many(conn, "event_results", results)
                upsert_many(conn, "body_parts", bparts)

                # ensure lookups exist before inserting events (FK safety)
                conn.commit()
                upsert_many(conn, "events", events)
                conn.commit()
                time.sleep(0.1)