




def increment_score(current_score: int, target_score: int, incr_speed=0.4) -> int:
    if current_score < target_score:
        return min(round(current_score + (target_score-current_score)*incr_speed + 0.5), target_score)
    else:
        return target_score