"Other stuff that I didn't know where else to put."


import random
import debug



def get_start_level() -> str:
    "Gets the name of the level to start the game on."
    return debug.Cheats.test_level or "level_1"


def increment_score(current_score: int, target_score: int, incr_speed=0.4) -> int:
    "Increments score based on incr_speed until it match target value."
    if current_score < target_score:
        return min(round(current_score + (target_score-current_score)*incr_speed + 0.5), target_score)
    else:
        return target_score
    


def level_completion_amount(score: int, score_range: tuple[int, int]) -> float:
    "Gives a value from 0 to 1 that shows how far along a level the player is."
    return (score-score_range[0])/(score_range[1]-score_range[0])


def weighted_choice[T](choices: tuple[list[T], list[int]]) -> T:
    return random.choices(*choices)[0]



def set_console_style(*style_codes: int) -> None:
    if not style_codes:
        style_codes = (0,)

    print(*(f"\033[{code}m" for code in style_codes), sep="", end="")


def bar_of_dashes() -> None:
    print("-"*80)



def find_subclass_by_name[T](base_class: type[T], class_name: str) -> type[T] | None:
    """
    Finds the first subclass of `class_type` that matches the `class_name`.
    """
    if base_class.__name__ == class_name:
        return base_class

    found = None
    for cls in base_class.__subclasses__():
        found = find_subclass_by_name(cls, class_name)
        if found is not None:
            return found