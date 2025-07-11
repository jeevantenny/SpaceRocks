from game_objects import GameObject, components



test_object = GameObject((0, 0), [components.ObjectVelocity(), components.ObjectGravity()])


test_object.accelerate((5, 5))
test_object.accelerate((5, 5))
for _ in range(5):
    test_object.update()

print(test_object.position)
print(test_object.get_velocity())