from manim import *
import os

from manim import *

class AdditiveColorMixing(Scene):
    def construct(self):
        # Create colors from Red-Green-Blue components.
        red = RED(color=RED)
        green = GREEN(color=GREEN)
        blue = BLUE(color=BLUE)

        # Show initial state - only one component at a time,
        # demonstrating pure primary colors before they mix together.

        self.play(Move(red).to_edge(LEFT))
        self.add(red)

        self.wait()

        self.play(
            Move(green).to_edge(RIGHT),
            FadeIn(green)
        )

        self.wait()

        self.play(FadeOut(green))

        self.wait()

        # Now let's add Blue into our scene!
        cyan = CYAN

        self.play(
            Combine(red + green, cyan)
        )


if __name__ == "__main__":
    from manim import config

    config.media_dir = os.getcwd()
    config.output_file = "BallTransformation"
    config.quality = "low_quality"

    AdditiveColorMixing().render()