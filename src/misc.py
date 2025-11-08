"Other stuff that I didn't know where else to put."



def increment_score(current_score: int, target_score: int, incr_speed=0.4) -> int:
    "Increments score based on incr_speed until it match target value."
    if current_score < target_score:
        return min(round(current_score + (target_score-current_score)*incr_speed + 0.5), target_score)
    else:
        return target_score
    


def level_completion_amount(score: int, score_range: tuple[int, int]) -> float:
    "Gives a value from 0 to 1 that shows how far along a level the player is."
    return (score-score_range[0])/(score_range[1]-score_range[0])