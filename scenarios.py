"""
scenarios.py - Master scenario registry for the Health Informatics Learning Platform.

Consolidates 300+ unique scenario templates from three part files:
  - scenarios_part1.py: Data Extraction, Data Quality, Compliance (100)
  - scenarios_part2.py: System, Analytics, Revenue Cycle, Clinical Ops (100)
  - scenarios_part3.py: Reporting, Communication, Documentation, Advanced (100)

Public API
----------
    get_all_scenarios()        -> list of all scenario dicts
    get_scenarios(filters)     -> filtered list
    get_scenario_categories()  -> list of category names with counts
"""

import random


def _safe_import(module_name, attr_name):
    """Import a scenario list, returning [] on failure."""
    try:
        mod = __import__(module_name)
        return getattr(mod, attr_name, [])
    except Exception:
        return []


def get_all_scenarios():
    """Return all scenario templates from all part files."""
    all_scenarios = []
    all_scenarios.extend(_safe_import("scenarios_part1", "SCENARIOS_PART1"))
    all_scenarios.extend(_safe_import("scenarios_part2", "SCENARIOS_PART2"))
    all_scenarios.extend(_safe_import("scenarios_part3", "SCENARIOS_PART3"))
    return all_scenarios


def get_scenarios(category=None, difficulty=None, role=None, tools=None,
                  min_minutes=None, max_minutes=None):
    """Return filtered scenario templates.

    Parameters
    ----------
    category : str, optional
        Filter by category name (case-insensitive substring match).
    difficulty : str, optional
        Filter by difficulty: beginner, intermediate, advanced.
    role : str, optional
        Filter to scenarios targeting a specific role.
    tools : list[str], optional
        Filter to scenarios that use any of the specified tools.
    min_minutes, max_minutes : int, optional
        Filter by estimated time range.
    """
    scenarios = get_all_scenarios()
    if category:
        cat_lower = category.lower()
        scenarios = [s for s in scenarios
                     if cat_lower in s.get("category", "").lower()]
    if difficulty:
        scenarios = [s for s in scenarios
                     if s.get("difficulty", "intermediate") == difficulty]
    if role:
        scenarios = [s for s in scenarios
                     if role in s.get("target_roles", [])]
    if tools:
        tool_set = set(tools)
        scenarios = [s for s in scenarios
                     if tool_set & set(s.get("tools", []))]
    if min_minutes is not None:
        scenarios = [s for s in scenarios
                     if s.get("estimated_minutes", 30) >= min_minutes]
    if max_minutes is not None:
        scenarios = [s for s in scenarios
                     if s.get("estimated_minutes", 30) <= max_minutes]
    return scenarios


def get_scenario_categories():
    """Return a summary of all categories with counts."""
    from collections import Counter
    scenarios = get_all_scenarios()
    cat_counts = Counter(s.get("category", "Unknown") for s in scenarios)
    return [{"category": cat, "count": count}
            for cat, count in sorted(cat_counts.items())]


def get_scenario_stats():
    """Return overall statistics about the scenario library."""
    scenarios = get_all_scenarios()
    from collections import Counter

    difficulties = Counter(s.get("difficulty", "intermediate") for s in scenarios)
    categories = Counter(s.get("category", "Unknown") for s in scenarios)
    tools_used = Counter()
    for s in scenarios:
        for t in s.get("tools", []):
            tools_used[t] += 1
    roles = Counter()
    for s in scenarios:
        for r in s.get("target_roles", []):
            roles[r] += 1

    minutes = [s.get("estimated_minutes", 30) for s in scenarios]

    return {
        "total_scenarios": len(scenarios),
        "by_difficulty": dict(difficulties),
        "by_category": dict(categories),
        "by_tool": dict(tools_used),
        "by_role": dict(roles),
        "time_range": {
            "min": min(minutes) if minutes else 0,
            "max": max(minutes) if minutes else 0,
            "avg": round(sum(minutes) / len(minutes), 1) if minutes else 0,
        },
    }


def select_scenarios_for_session(role, difficulty, task_count,
                                 task_time_target_minutes):
    """Select a balanced set of scenarios for a shift session.

    Tries to pick scenarios matching the role and difficulty, with a mix
    of categories and tools. Falls back to any available scenarios if
    filters are too restrictive.
    """
    # First try: exact match on role and difficulty
    pool = get_scenarios(role=role, difficulty=difficulty)

    # Fallback: relax difficulty
    if len(pool) < task_count:
        pool = get_scenarios(role=role)

    # Fallback: relax role too
    if len(pool) < task_count:
        pool = get_scenarios(difficulty=difficulty)

    # Final fallback: all scenarios
    if len(pool) < task_count:
        pool = get_all_scenarios()

    if not pool:
        return []

    # Try to get category diversity
    random.shuffle(pool)
    selected = []
    seen_categories = set()

    # First pass: one from each category
    for s in pool:
        cat = s.get("category", "")
        if cat not in seen_categories and len(selected) < task_count:
            selected.append(s)
            seen_categories.add(cat)

    # Second pass: fill remaining slots
    for s in pool:
        if s not in selected and len(selected) < task_count:
            selected.append(s)

    return selected[:task_count]
