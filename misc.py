from custom_types import TextureMap





def get_named_frames(frames: TextureMap, name: str) -> TextureMap:
    length = len(name)

    return {
        frame_name.removeprefix(f"{name}_"): frame

        for frame_name, frame in frames.items()
        if frame_name[0:length] == name
    }




def instructions_text() ->  str:
    return f"Forward [w]     Shoot [space]     Turn [a]-[d]"



def increment_score(current_score: int, target_score: int, incr_speed=0.4) -> int:
    return min(round(current_score + (target_score-current_score)*incr_speed + 0.5), target_score)